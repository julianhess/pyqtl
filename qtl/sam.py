import pandas as pd
import numpy as np
import subprocess
import io




def is_stranded(bam_file, verbose=False):
    """
    Determine whether the sequencing protocol was strand-specific
    based on reads mapping to ACTB(-) and FTL(+)
    """

    header = subprocess.check_output(f'samtools view -H {bam_file}', shell=True).decode()
    header = header.strip().split('\n')
    header = [i.split('\t') for i in header if i.startswith('@SQ')]
    c = [i[1].split(':')[1] for i in header]
    if not np.any([i.startswith('chr') for i in c]):  # assume hg19
        plus_str = '19:49468558-49470135'  # FTL
        minus_str = '7:5566782-5603415'  # ACTB
    else:  # hg38
        plus_str = 'chr19:48965301-48966878'  # FTL
        minus_str = 'chr7:5527151-5563784'  # ACTB

    cmd = f'samtools view -f2 -F3840 {bam_file} {plus_str} | cut -f2 | sort | uniq -c'
    s = subprocess.check_output(cmd, shell=True).decode()
    dfp = pd.read_csv(io.StringIO(s), sep='\s+', header=None, names=['count', 'flag']).set_index('flag').squeeze()

    cmd = f'samtools view -f2 -F3840 {bam_file} {minus_str} | cut -f2 | sort | uniq -c'
    s = subprocess.check_output(cmd, shell=True).decode()
    dfm = pd.read_csv(io.StringIO(s), sep='\s+', header=None, names=['count', 'flag']).set_index('flag').squeeze()

    dfp = dfp.reindex([147, 99, 83, 163], fill_value=0)
    dfm = dfm.reindex([147, 99, 83, 163], fill_value=0)

    p = (dfp[[147, 99]].sum() / dfp.sum())
    m = (dfm[[163, 83]].sum() / dfm.sum())
    is_stranded = (p<0.02) & (m<0.02)
    if verbose:
        print(f'Total read coverage: {dfp.sum()} (FTL), {dfm.sum()} (ACTB)')
        print(f'Proportion of FTL(+)  reads on -strand: {p:.4g}')
        print(f'Proportion of ACTB(-) reads on +strand: {m:.4g}')
        print(f'Stranded: {is_stranded}')
    return is_stranded
