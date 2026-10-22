"""Descriptive publication figure from saved results only; no inference."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent


def main():
    source=HERE/'transfer_reading/results.json'
    results=json.loads(source.read_text())
    order=('ordinary','book','guide','unrelated')
    names={'ordinary':'Ordinary profile','book':'Book reading','guide':'Operational guide','unrelated':'Unrelated reading'}
    groups={r['arm']:r for r in results['summary']}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
                        'axes.spines.right':False,'axes.labelcolor':'#28343b','text.color':'#28343b'})
    fig,(left,right)=plt.subplots(1,2,figsize=(10,4.4),gridspec_kw={'width_ratios':[1.1,1]})
    values=[groups[a]['primary_successes']/16 for a in order]
    left.barh(range(4),values,color=['#a4adb1','#315f71','#6f8d8a','#b2a38e'],height=.56)
    left.set_yticks(range(4),[names[a] for a in order]);left.invert_yaxis()
    left.set_xlim(0,1.14);left.set_xticks([0,.25,.5,.75,1],['0','25','50','75','100'])
    for i,a in enumerate(order):left.text(values[i]+.025,i,f"{groups[a]['primary_successes']}/16",va='center',fontsize=9)
    left.set_xlabel('Predeclared primary success (%)');left.set_title('A  Optimal plans submitted',loc='left',fontweight='bold',pad=16)
    comparisons=results['paired']
    for i,row in enumerate(comparisons):
        low,high=row['descriptive_cluster_bootstrap_95_percentile'];point=row['difference']
        right.plot([low,high],[i,i],color='#315f71',linewidth=2)
        right.plot(point,i,'o',color='#315f71',markersize=5)
    right.axvline(0,color='#a4adb1',linewidth=.8,linestyle='--')
    right.set_yticks(range(3),['Book minus '+names[r['b']].lower() for r in comparisons]);right.invert_yaxis()
    right.set_xlim(-1.05,1.05);right.set_xticks([-1,-.5,0,.5,1],['-100','-50','0','50','100'])
    right.set_xlabel('Paired difference (percentage points)')
    right.set_title('B  Four source-seed clusters',loc='left',fontweight='bold',pad=16)
    fig.suptitle('Reading-mediated transfer on one authored planning class',fontsize=12,fontweight='bold',y=.98)
    fig.text(.02,.055,'Primary omits exact citation closure. Fully traced optimal plans: ordinary 0/16, book 0/16, guide 1/16, unrelated 0/16.',fontsize=8,color='#58666d')
    fig.text(.02,.015,'Intervals: descriptive four-cluster bootstrap percentiles, not population guarantees. Every condition has 16 episodes.',fontsize=8,color='#58666d')
    fig.tight_layout(rect=[0,.12,1,.93],w_pad=3)
    output=HERE/'reading-transfer-results.png'
    fig.savefig(output,dpi=220,facecolor='white',metadata={'Software':'AI Ontology descriptive research figure'})
    plt.close(fig)
    script=Path(__file__).resolve()
    manifest={'schema':'reading-transfer-figure/1','matplotlib':matplotlib.__version__,
              'inputs':{'research/transfer_reading/results.json':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'research/plot_reading_transfer.py':hashlib.sha256(script.read_bytes()).hexdigest()},
              'output':'research/reading-transfer-results.png','output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    (HERE/'reading-transfer-figure.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'figure':manifest['output'],'bytes':output.stat().st_size}))


if __name__=='__main__':main()
