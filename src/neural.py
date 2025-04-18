# -*- coding: utf-8 -*-

# CMU 11424/11824 Spring 2024: Reinflection and Paradigm Completion

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/
!rm -rf dataset
!unzip dataset.zip

"""## Performance Measures

Here, we are using exact match for evaluation.
"""

import unicodedata

def evaluate(gold, pred):

  preds = [int(unicodedata.normalize("NFC",p)==unicodedata.normalize("NFC",g)) for p, g in zip(pred, gold)]
  if len(preds) == 0:
    return 0
  return sum(preds)/len(preds)

"""## Non-Neural Baseline

This method is pulled from the Unimorph non-neural baseline for Sigmorphon Reinflection Shared Task 2022.
"""

import sys, os, getopt, re
from functools import wraps
from glob import glob
def hamming(s,t):
    return sum(1 for x,y in zip(s,t) if x != y)


def halign(s,t):
    """Align two strings by Hamming distance."""
    slen = len(s)
    tlen = len(t)
    minscore = len(s) + len(t) + 1
    for upad in range(0, len(t)+1):
        upper = '_' * upad + s + (len(t) - upad) * '_'
        lower = len(s) * '_' + t
        score = hamming(upper, lower)
        if score < minscore:
            bu = upper
            bl = lower
            minscore = score

    for lpad in range(0, len(s)+1):
        upper = len(t) * '_' + s
        lower = (len(s) - lpad) * '_' + t + '_' * lpad
        score = hamming(upper, lower)
        if score < minscore:
            bu = upper
            bl = lower
            minscore = score

    zipped = zip(bu,bl)
    newin  = ''.join(i for i,o in zipped if i != '_' or o != '_')
    newout = ''.join(o for i,o in zipped if i != '_' or o != '_')
    return newin, newout


def levenshtein(s, t, inscost = 1.0, delcost = 1.0, substcost = 1.0):
    """Recursive implementation of Levenshtein, with alignments returned."""
    @memolrec
    def lrec(spast, tpast, srem, trem, cost):
        if len(srem) == 0:
            return spast + len(trem) * '_', tpast + trem, '', '', cost + len(trem)
        if len(trem) == 0:
            return spast + srem, tpast + len(srem) * '_', '', '', cost + len(srem)

        addcost = 0
        if srem[0] != trem[0]:
            addcost = substcost

        return min((lrec(spast + srem[0], tpast + trem[0], srem[1:], trem[1:], cost + addcost),
                   lrec(spast + '_', tpast + trem[0], srem, trem[1:], cost + inscost),
                   lrec(spast + srem[0], tpast + '_', srem[1:], trem, cost + delcost)),
                   key = lambda x: x[4])

    answer = lrec('', '', s, t, 0)
    return answer[0],answer[1],answer[4]


def memolrec(func):
    """Memoizer for Levenshtein."""
    cache = {}
    @wraps(func)
    def wrap(sp, tp, sr, tr, cost):
        if (sr,tr) not in cache:
            res = func(sp, tp, sr, tr, cost)
            cache[(sr,tr)] = (res[0][len(sp):], res[1][len(tp):], res[4] - cost)
        return sp + cache[(sr,tr)][0], tp + cache[(sr,tr)][1], '', '', cost + cache[(sr,tr)][2]
    return wrap


def alignprs(lemma, form):
    """Break lemma/form into three parts:
    IN:  1 | 2 | 3
    OUT: 4 | 5 | 6
    1/4 are assumed to be prefixes, 2/5 the stem, and 3/6 a suffix.
    1/4 and 3/6 may be empty.
    """

    al = levenshtein(lemma, form, substcost = 1.1) # Force preference of 0:x or x:0 by 1.1 cost
    alemma, aform = al[0], al[1]
    # leading spaces
    lspace = max(len(alemma) - len(alemma.lstrip('_')), len(aform) - len(aform.lstrip('_')))
    # trailing spaces
    tspace = max(len(alemma[::-1]) - len(alemma[::-1].lstrip('_')), len(aform[::-1]) - len(aform[::-1].lstrip('_')))
    return alemma[0:lspace], alemma[lspace:len(alemma)-tspace], alemma[len(alemma)-tspace:], aform[0:lspace], aform[lspace:len(alemma)-tspace], aform[len(alemma)-tspace:]


def prefix_suffix_rules_get(lemma, form):
    """Extract a number of suffix-change and prefix-change rules
    based on a given example lemma+inflected form."""
    lp,lr,ls,fp,fr,fs = alignprs(lemma, form) # Get six parts, three for in three for out

    # Suffix rules
    ins  = lr + ls + ">"
    outs = fr + fs + ">"
    srules = set()
    for i in range(min(len(ins), len(outs))):
        srules.add((ins[i:], outs[i:]))
    srules = {(x[0].replace('_',''), x[1].replace('_','')) for x in srules}

    # Prefix rules
    prules = set()
    if len(lp) >= 0 or len(fp) >= 0:
        inp = "<" + lp
        outp = "<" + fp
        for i in range(0,len(fr)):
            prules.add((inp + fr[:i],outp + fr[:i]))
            prules = {(x[0].replace('_',''), x[1].replace('_','')) for x in prules}

    return prules, srules


def apply_best_rule(lemma, msd, allprules, allsrules):
    """Applies the longest-matching suffix-changing rule given an input
    form and the MSD. Length ties in suffix rules are broken by frequency.
    For prefix-changing rules, only the most frequent rule is chosen."""

    bestrulelen = 0
    base = "<" + lemma + ">"
    if msd not in allprules and msd not in allsrules:
        return lemma # Haven't seen this inflection, so bail out

    if msd in allsrules:
        applicablerules = [(x[0],x[1],y) for x,y in allsrules[msd].items() if x[0] in base]
        if applicablerules:
            bestrule = max(applicablerules, key = lambda x: (len(x[0]), x[2], len(x[1])))
            base = base.replace(bestrule[0], bestrule[1])

    if msd in allprules:
        applicablerules = [(x[0],x[1],y) for x,y in allprules[msd].items() if x[0] in base]
        if applicablerules:
            bestrule = max(applicablerules, key = lambda x: (x[2]))
            base = base.replace(bestrule[0], bestrule[1])

    base = base.replace('<', '')
    base = base.replace('>', '')
    return base


def numleadingsyms(s, symbol):
    return len(s) - len(s.lstrip(symbol))


def numtrailingsyms(s, symbol):
    return len(s) - len(s.rstrip(symbol))

lang = 'swc'

allprules, allsrules = {}, {}
lines = [line.strip() for line in open(f"dataset/{lang}.train.tsv", "r") if line != '\n']
trainlemmas = set()
trainmsds = set()

# First, test if language is predominantly suffixing or prefixing
# If prefixing, work with reversed strings
prefbias, suffbias = 0,0
for l in lines:
  lemma, form, msd = l.split(u'\t')
  trainlemmas.add(lemma)
  trainmsds.add(msd)
  aligned = halign(lemma, form)
  if ' ' not in aligned[0] and ' ' not in aligned[1] and '-' not in aligned[0] and '-' not in aligned[1]:
      prefbias += numleadingsyms(aligned[0],'_') + numleadingsyms(aligned[1],'_')
      suffbias += numtrailingsyms(aligned[0],'_') + numtrailingsyms(aligned[1],'_')
for l in lines: # Read in lines and extract transformation rules from pairs
    lemma, form, msd = l.split(u'\t')
    if prefbias > suffbias:
        lemma = lemma[::-1]
        form = form[::-1]
    prules, srules = prefix_suffix_rules_get(lemma, form)

    if msd not in allprules and len(prules) > 0:
        allprules[msd] = {}
    if msd not in allsrules and len(srules) > 0:
        allsrules[msd] = {}

    for r in prules:
        if (r[0],r[1]) in allprules[msd]:
            allprules[msd][(r[0],r[1])] = allprules[msd][(r[0],r[1])] + 1
        else:
            allprules[msd][(r[0],r[1])] = 1

    for r in srules:
        if (r[0],r[1]) in allsrules[msd]:
            allsrules[msd][(r[0],r[1])] = allsrules[msd][(r[0],r[1])] + 1
        else:
            allsrules[msd][(r[0],r[1])] = 1

evallines = [line.strip() for line in open(f"dataset/{lang}.testhidden.tsv", "r") if line != '\n']
outfile = open(f"{lang}.txt", "w")

pred = []
gold = []

for l in evallines:
    lemma, correct, msd = l.split(u'\t')
    if prefbias > suffbias:
        lemma = lemma[::-1]
    outform = apply_best_rule(lemma, msd, allprules, allsrules)
    if prefbias > suffbias:
        outform = outform[::-1]
        lemma = lemma[::-1]
    pred.append(outform)
    gold.append(correct)

    outfile.write(outform + "\n")

print(pred[:10])
print(gold[:10])
print(evaluate(pred, gold))

"""## Neural Baseline

This method is pulled from the Unimorph non-neural baseline for Sigmorphon Reinflection Shared Task 2022.
"""

!git clone https://github.com/shijie-wu/neural-transducer/

!pip install --upgrade torch==1.13.1

# Commented out IPython magic to ensure Python compatibility.
run_train = """
#!/bin/bash
lang=$1
arch=${2:-tagtransformer}
suff=$3

lr=0.001
scheduler=warmupinvsqr
epochs=10
warmup=100
beta2=0.98       # 0.999
label_smooth=0.1 # 0.0
total_eval=50
bs=400 # 256

# transformer
layers=4
hs=1024
embed_dim=256
nb_heads=4
#dropout=${2:-0.3}
dropout=0.3
ckpt_dir=checkpoints/sig22


path=/content

python src/train.py \
    --dataset sigmorphon17task1 \
    --train $path/$lang.train.tsv \
    --dev $path/$lang.dev.tsv \
    --test $path/$lang.test_transformed.tsv \
    --model $ckpt_dir/$arch/$lang \
    --decode greedy --max_decode_len 32 \
    --embed_dim $embed_dim --src_hs $hs --trg_hs $hs --dropout $dropout --nb_heads $nb_heads \
    --label_smooth $label_smooth --total_eval $total_eval \
    --src_layer $layers --trg_layer $layers --max_norm 1 --lr $lr --shuffle \
    --arch $arch --gpuid 0 --estop 1e-8 --bs $bs --epochs $epochs \
    --scheduler $scheduler --warmup_steps $warmup --cleanup_anyway --beta2 $beta2 --bestacc
"""

# %cd neural-transducer/
with open('run_train.sh', 'w') as f:
  f.write(run_train)
!make
!bash run_train.sh xty

# This function adds a dummy second column to your test set so that you can use the below decoding script to get predictions!
# https://github.com/shijie-wu/neural-transducer/blob/master/src/sigmorphon19-task1-decode.py

import csv

language = 'xty'

def insert_column(input_tsv, output_tsv):
    with open(input_tsv, 'r', newline='', encoding='utf-8') as infile, \
         open(output_tsv, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.reader(infile, delimiter='\t')
        writer = csv.writer(outfile, delimiter='\t')

        for row in reader:
            if len(row) > 1:  # Ensure there are at least two columns
                new_row = [row[0], '#'] + row[1:]
            else:
                new_row = row + ['#']  # Edge case where only one column exists
            writer.writerow(new_row)

# Usage
insert_column(f'/content/{language}.test.tsv', f'/content/{language}.test_transformed.tsv')

import csv

# 파일 경로 설정
input_file = "/content/neural-transducer/checkpoints/sig22/tagtransformer/xty.decode.test.tsv"
output_file = "/content/neural-transducer/checkpoints/sig22/tagtransformer/xty_first_column_cleaned.txt"

# 첫 번째 컬럼만 추출하여 저장 (첫 번째 행 제거 + 문자 사이 공백 제거)
with open(input_file, "r", encoding="utf-8") as tsv_file, open(output_file, "w", encoding="utf-8") as txt_file:
    reader = csv.reader(tsv_file, delimiter="\t")
    next(reader)  # 첫 번째 행 제거

    for row in reader:
        if row:  # 빈 줄 방지
            cleaned_text = "".join(row[0].split())  # 문자 사이 공백 제거
            txt_file.write(cleaned_text + "\n")

print(f"✅ 첫 번째 행 제거 후 {output_file} 파일로 저장 완료!")
