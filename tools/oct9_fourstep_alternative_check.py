"""Independent rule-order enumeration for two changed isolated Queen choices.

This is a complete-known-fixture oracle, not a replay or a full match.
Movement order follows official engine/src/actions.cc Move and Step.
"""
from itertools import product
from pathlib import Path
import json

D = {'N':(0,-1),'E':(1,0),'S':(0,1),'W':(-1,0)}

def move(body, path, pearls, other):
    body=list(body); pearls=set(pearls); quota=(len(body)+3)//4
    for step, direction in enumerate(path):
        paid=step>=quota
        if paid and len(body)<=2:return 'unaffordable',body,pearls
        dx,dy=D[direction]; p=((body[0][0]+dx)%20,(body[0][1]+dy)%20)
        if p in body:return 'self',body,pearls
        if p in other:return ('head' if p==other[0] else 'other-body'),body,pearls
        body.insert(0,p)
        if p in pearls:pearls.remove(p)
        else:body.pop()
        if paid:body.pop()
    return 'alive',body,pearls

def attacks(enemy, queen, pearls):
    found=[]
    for n in range(1,5):
        for path in product(D,repeat=n):
            path=''.join(path)
            if any(path.startswith(done) for done in found):continue
            if move(enemy,path,pearls,queen)[0]=='head':found.append(path)
    return found

def main():
    report=[]
    for name, enemy, pearls, actual in [
        ('partial-enemy',[(3,7),(2,7),(1,7)],[(4,6)],'WWW'),
        ('visible-two-step-ambush',[(3,7),(3,8),(3,9)],[(3,6)],'NN'),
    ]:
        row={'name':name,'actual_choice':actual,'actual_enemy_length':len(enemy),'choices':[]}
        for action in [actual,'N','W']:
            status,body,left=move([(5,6),(6,6),(6,7)],action,pearls,enemy)
            paths=attacks(enemy,body,left) if status=='alive' else []
            row['choices'].append({'action':action,'status':status,'body':body,
                                   'enemy_attacks_up_to_four':paths})
        assert row['choices'][0]['status']=='alive'
        assert not row['choices'][0]['enemy_attacks_up_to_four']
        assert row['choices'][2]['enemy_attacks_up_to_four']
        report.append(row)
    out=Path('test-results/oct9-last30/v270-queen-alternative-rule-check.json')
    out.write_text(json.dumps({'scope':'Isolated open-board physical oracle derived from official Move/Step; uses stated complete fixture enemy bodies, not unknown production body guesses. Does not establish long-term survival or Elo.', 'rows':report},indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
