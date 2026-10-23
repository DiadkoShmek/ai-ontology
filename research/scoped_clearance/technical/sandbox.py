"""One controller step in a fresh Linux bubblewrap namespace.

Contract: source defines ``controller(request)`` and returns one JSON value.
Only source, request and this fixed harness enter the bundle; the experiment's
tools, corpus, grading and oracle stay outside it. Captured output is untrusted.

This is cooperative local confinement, not a hardened multi-user service or a
Python-language sandbox. It trusts the host kernel, bubblewrap, libseccomp and
the read-only system Python/runtime mounts. It has no unrestricted fallback.
RLIMIT_AS limits process virtual address space, not aggregate kernel memory.
Unused SysV IPC and POSIX mqueue syscalls are denied to close their allocation
path; this is not a cgroup or a hard aggregate-memory guarantee.
Seccomp construction follows upstream seccomp_rule_add(3)/seccomp_export_bpf(3):
https://github.com/seccomp/libseccomp/tree/main/doc/man/man3
Bubblewrap policy boundary: https://github.com/containers/bubblewrap#sandbox-security
"""

import ctypes
import errno
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time


LIMITS = {
    "source_bytes": 65_536,
    "request_bytes": 262_144,
    "output_bytes": 65_536,  # combined stdout + stderr, never per-stream
    "json_depth": 32,
    "json_nodes": 20_000,
    "wall_seconds": 3.0,
    "cpu_seconds": 2,
    "address_space_bytes": 268_435_456,
    "file_bytes": 65_536,
    "tmpfs_bytes": 8_388_608,
    "open_files": 32,
}

_HARNESS = """import json, runpy
request = json.load(open('/bundle/request.json', encoding='utf-8'))
namespace = runpy.run_path('/bundle/controller.py', run_name='controller_module')
result = namespace['controller'](request)
print(json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(',', ':')))
"""

# Deny process/thread creation, networking (including Unix sockets), namespace
# changes, cross-process inspection and the host's inherited keyring API.
# A new PID/session namespace does not isolate Linux session keyrings.
# Initial execve must remain available:
# bubblewrap installs this filter immediately before executing system Python.
# A controller can replace itself with another mounted executable; the same
# kernel namespaces, filter, rlimits and external wall/output limits remain.
_DENIED_SYSCALLS = (
    "fork", "vfork", "clone", "clone3", "socket", "socketpair", "connect",
    "bind", "listen", "accept", "accept4", "sendto", "sendmsg", "sendmmsg",
    "recvfrom", "recvmsg", "recvmmsg", "shutdown", "getsockname",
    "getpeername", "getsockopt", "setsockopt", "unshare", "setns", "mount",
    "umount2", "pivot_root", "ptrace", "process_vm_readv", "process_vm_writev",
    "pidfd_getfd", "bpf", "perf_event_open", "userfaultfd", "io_uring_setup",
    "open_by_handle_at", "name_to_handle_at", "reboot", "kexec_load",
    "kexec_file_load", "init_module", "finit_module", "delete_module",
    "keyctl", "add_key", "request_key",
    "shmget", "shmat", "shmdt", "shmctl", "msgget", "msgsnd", "msgrcv",
    "msgctl", "semget", "semop", "semtimedop", "semctl", "mq_open",
    "mq_unlink", "mq_timedsend", "mq_timedreceive", "mq_notify", "mq_getsetattr",
)
# These entrypoints are native only on some architectures. Negative libseccomp
# pseudo-numbers mean they are absent on this native ABI, not a usable syscall.
# The filter's architecture check rejects foreign ABIs; do not add them here.
_OPTIONAL_NATIVE_IPC = (
    "ipc", "semtimedop_time64", "mq_timedsend_time64", "mq_timedreceive_time64",
)


def _json_bytes(value):
    """Reject non-JSON, cycles, nonfinite/deep/wide inputs before serialization."""
    active = set()
    count = 0
    string_bytes = 0

    def visit(item, depth):
        nonlocal count, string_bytes
        count += 1
        if count > LIMITS["json_nodes"] or depth > LIMITS["json_depth"]:
            raise ValueError("json-complexity")
        kind = type(item)
        if item is None or kind is bool:
            return
        if kind is int:
            if item.bit_length() > 4096:
                raise ValueError("json-integer")
            return
        if kind is float:
            if not math.isfinite(item):
                raise ValueError("json-nonfinite")
            return
        if kind is str:
            if len(item) > LIMITS["request_bytes"]:
                raise ValueError("json-string-size")
            string_bytes += len(item.encode("utf-8", "strict"))
            if string_bytes > LIMITS["request_bytes"]:
                raise ValueError("json-string-size")
            return
        if kind not in (list, dict):
            raise ValueError("json-type")
        if id(item) in active:
            raise ValueError("json-cycle")
        active.add(id(item))
        if kind is dict:
            for key, child in item.items():
                if type(key) is not str:
                    raise ValueError("json-key")
                visit(key, depth + 1)
                visit(child, depth + 1)
        else:
            for child in item:
                visit(child, depth + 1)
        active.remove(id(item))

    visit(value, 0)
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii")


def _export_filter(file):
    """Build native-architecture BPF; absent library/syscall/filter refuses."""
    lib = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.restype = None
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                         ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
    lib.seccomp_rule_add_array.restype = ctypes.c_int
    lib.seccomp_export_bpf.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.seccomp_export_bpf.restype = ctypes.c_int
    context = lib.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    if not context:
        raise OSError("seccomp-init")
    try:
        for name in _DENIED_SYSCALLS + _OPTIONAL_NATIVE_IPC:
            number = lib.seccomp_syscall_resolve_name(name.encode("ascii"))
            if name in _OPTIONAL_NATIVE_IPC and number < 0:
                continue
            if number == -1:
                raise OSError("seccomp-unresolved:" + name)
            action = 0x00050000 | errno.EPERM  # SCMP_ACT_ERRNO(EPERM)
            if lib.seccomp_rule_add_array(context, action, number, 0, None) != 0:
                raise OSError("seccomp-rule:" + name)
        if lib.seccomp_export_bpf(context, file.fileno()) != 0:
            raise OSError("seccomp-export")
        if os.fstat(file.fileno()).st_size == 0:
            raise OSError("seccomp-empty")
        os.lseek(file.fileno(), 0, os.SEEK_SET)
    finally:
        lib.seccomp_release(context)


def _command(bundle, filter_fd):
    # Absolute trusted binaries; no PATH lookup, shell, preexec_fn, host HOME,
    # project mount or network-enabled fallback. prlimit applies *hard* limits
    # before bubblewrap or submitted code can run.
    command = [
        "/usr/bin/prlimit",
        f"--as={LIMITS['address_space_bytes']}",
        f"--cpu={LIMITS['cpu_seconds']}",
        f"--fsize={LIMITS['file_bytes']}",
        f"--nofile={LIMITS['open_files']}", "--core=0", "--stack=8388608", "--",
        "/usr/bin/bwrap", "--unshare-all", "--unshare-user", "--disable-userns",
        "--die-with-parent", "--new-session", "--cap-drop", "ALL",
        "--clearenv", "--setenv", "LANG", "C.UTF-8",
        "--setenv", "HOME", "/nonexistent", "--setenv", "PATH", "/usr/bin",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64", "--proc", "/proc",
        "--remount-ro", "/proc", "--dev", "/dev", "--remount-ro", "/dev",
        "--size", str(LIMITS["tmpfs_bytes"]), "--tmpfs", "/tmp",
        "--ro-bind", str(bundle), "/bundle", "--chdir", "/tmp",
        "--seccomp", str(filter_fd), "--remount-ro", "/",
        "/usr/bin/python3", "-I", "-S", "-B", "/bundle/harness.py",
    ]
    return command


def _kill_owned(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _capture(command, filter_fd):
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env={}, pass_fds=(filter_fd,), start_new_session=True)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    error = None
    total = 0
    selector = selectors.DefaultSelector()
    try:
        for name in buffers:
            stream = getattr(process, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map() or process.poll() is None:
            remaining = LIMITS["wall_seconds"] - (time.monotonic() - started)
            if remaining <= 0:
                error = "wall-limit"
                _kill_owned(process)
                break
            for key, _ in selector.select(min(remaining, 0.05)):
                chunk = os.read(key.fileobj.fileno(), 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                available = LIMITS["output_bytes"] - total
                buffers[key.data].extend(chunk[:available])
                total += min(len(chunk), available)
                if len(chunk) > available:
                    error = "output-limit"
                    _kill_owned(process)
                    break
            if error:
                break
        try:
            returncode = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            _kill_owned(process)
            returncode = process.wait(timeout=1)
    finally:
        if process.poll() is None:
            _kill_owned(process)
            process.wait(timeout=1)
        selector.close()
        process.stdout.close()
        process.stderr.close()
    try:
        stdout = bytes(buffers["stdout"]).decode("utf-8", "strict")
    except UnicodeError:
        stdout = bytes(buffers["stdout"]).decode("utf-8", "replace")
        error = error or "invalid-output"
    stderr = bytes(buffers["stderr"]).decode("utf-8", "replace")
    return {"terminal": None, "error": error, "stdout": stdout,
            "stderr": stderr, "returncode": returncode,
            "wall_seconds": time.monotonic() - started, "limits": dict(LIMITS)}


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate-output-key")
        value[key] = item
    return value


def run_controller(source, request):
    """Execute once; every refusal/error has terminal=None and bounded capture.

    No caller-controlled paths or mounts are accepted. Error strings distinguish
    input refusal, unavailable confinement, child failure and invalid output.
    A successful JSON result is a submitted action proposal, never permission.
    """
    empty = {"terminal": None, "error": None, "stdout": "", "stderr": "",
             "returncode": None, "wall_seconds": 0.0, "limits": dict(LIMITS)}
    try:
        if type(source) is not str:
            raise ValueError("source-type")
        if len(source) > LIMITS["source_bytes"]:
            raise ValueError("source-size")
        source_bytes = source.encode("utf-8", "strict")
        if len(source_bytes) > LIMITS["source_bytes"]:
            raise ValueError("source-size")
        request_bytes = _json_bytes(request)
        if len(request_bytes) > LIMITS["request_bytes"]:
            raise ValueError("request-size")
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        empty["error"] = "input-refused:" + str(exc)[:160]
        return empty
    try:
        with tempfile.TemporaryDirectory(prefix="document-controller-") as folder:
            bundle = Path(folder)
            (bundle / "controller.py").write_bytes(source_bytes)
            (bundle / "request.json").write_bytes(request_bytes)
            (bundle / "harness.py").write_text(_HARNESS, encoding="utf-8")
            with tempfile.TemporaryFile() as filter_file:
                _export_filter(filter_file)
                result = _capture(_command(bundle, filter_file.fileno()),
                                  filter_file.fileno())
    except (OSError, subprocess.SubprocessError) as exc:
        empty["error"] = "confinement-unavailable:" + type(exc).__name__
        return empty
    if result["error"] is not None:
        return result
    if result["returncode"] != 0:
        result["error"] = "process-exit"
        return result
    try:
        terminal = json.loads(result["stdout"], object_pairs_hook=_unique_object)
        _json_bytes(terminal)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        result["error"] = "invalid-output"
        return result
    result["terminal"] = terminal
    return result
