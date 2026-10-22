"""Rebuild the descriptive figure from the frozen follow-up scores."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/'continuity_pilot_v2/results.json').read_text())['summary']
colors=['#6c7780','#b07849','#315b70','#4e8479']
fig,axes=plt.subplots(1,2,figsize=(9,3.5),constrained_layout=True)
for ax,model,title in zip(axes,['qwen3:4b-instruct-2507-q4_K_M','granite3.3:2b'],
                         ['Qwen3 4B Instruct 2507','Granite 3.3 2B']):
    groups=[r for r in rows if r['model']==model]
    bars=ax.bar(range(4),[r['correct'] for r in groups],color=colors,width=.65)
    ax.set(ylim=(0,26),yticks=[0,6,12,18,24],xticks=range(4),
           xticklabels=['Journal','Ontology\nwrapper','Compiled','Simple\nindex'],
           title=title,ylabel='Exact decisions / 24 authored cases')
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
    for bar,r in zip(bars,groups):
        ax.text(bar.get_x()+bar.get_width()/2,r['correct']+.5,str(r['correct']),ha='center',fontsize=11)
fig.suptitle('Exploratory schema-guided cohort · six dependent scenario families',fontsize=11)
fig.savefig(HERE/'continuity-results.png',dpi=190,facecolor='white')
plt.close(fig)
