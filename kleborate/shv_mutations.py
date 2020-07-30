"""
Copyright 2020 Kat Holt
Copyright 2020 Ryan Wick (rrwick@gmail.com)
https://github.com/katholt/Kleborate/

This file is part of Kleborate. Kleborate is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version. Kleborate is distributed in
the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details. You should have received a copy of the GNU General Public License along with Kleborate. If
not, see <http://www.gnu.org/licenses/>.
"""

from Bio.Seq import Seq
from Bio.Alphabet import IUPAC
from Bio import pairwise2
from Bio.SubsMat.MatrixInfo import blosum62


def check_for_shv_mutations(hit, hit_allele, bla_class):
    # Don't do anything on non-SHV genes.
    if 'SHV' not in hit_allele:
        return bla_class, [], [], None

    nucl_seq, _, _ = hit.get_seq_start_end_pos_strand()

    # If there are any ambiguous bases in the sequence, then we can't do the translation.
    ambiguous_bases = set(b for b in nucl_seq) - {'A', 'C', 'G', 'T'}
    if ambiguous_bases:
        return bla_class, [], [], None

    # BioPython doesn't like it if the sequence isn't a multiple of 3.
    nucl_seq = nucl_seq[:len(nucl_seq) // 3 * 3]

    coding_dna = Seq(nucl_seq, IUPAC.unambiguous_dna)
    translation = str(coding_dna.translate(table='Bacterial', to_stop=True))

    shv_1_ref = 'MRYIRLCIISLLATLPLAVHASPQPLEQIKLSESQLSGRVGMIEMDLASGRTLTAWRADERFPMMSTFKVVLCGAVLAR' \
                'VDAGDEQLERKIHYRQQDLVDYSPVSEKHLADGMTVGELCAAAITMSDNSAANLLLATVGGPAGLTAFLRQIGDNVTRL' \
                'DRWETELNEALPGDARDTTTPASMAATLRKLLTSQRLSARSQRQLLQWMVDDRVAGPLIRSVLPAGWFIADKTGAGERG' \
                'ARGIVALLGPNNKAERIVVIYLRDTPASMAERNQQIAGIGAALIEHWQR'

    alignments = pairwise2.align.globalds(shv_1_ref, translation, blosum62, -10, -0.5)
    alignment = alignments[0]
    ref_aligned, hit_aligned, score, _, _ = alignment

    # If the identity of the alignment is too low, then it's not appropriate to look for SHV
    # mutations in this hit.
    identity = get_percent_identity(ref_aligned, hit_aligned)
    if identity < 0.9:
        return bla_class, [], [], None

    class_changing_mutations = []

    # Mutations at these sites will lead to an ESBL class:
    pos_169_mut, pos_169_aa = get_mut(ref_aligned, hit_aligned, 164, 169, 'L')
    pos_179_mut, pos_179_aa = get_mut(ref_aligned, hit_aligned, 174, 179, 'D')
    pos_238_mut, pos_238_aa = get_mut(ref_aligned, hit_aligned, 233, 238, 'G')
    if (pos_169_mut or pos_179_mut or pos_238_mut) and bla_class != 'Bla_ESBL':
        bla_class = 'Bla_ESBL'
        class_changing_mutations += [pos_169_mut, pos_179_mut, pos_238_mut]

    # Mutations at site Ambler-148 will lead to an ESBL class, but only if site Ambler-39 is Q.
    pos_039_mut, pos_039_aa = get_mut(ref_aligned, hit_aligned,  34,  39, 'Q')
    pos_148_mut, pos_148_aa = get_mut(ref_aligned, hit_aligned, 143, 148, 'L')
    if (pos_148_mut and pos_039_mut == '') and bla_class != 'Bla_ESBL':
        bla_class = 'Bla_ESBL'
        class_changing_mutations += [pos_148_mut]

    # Mutations at these sites will lead to inhibition:
    pos_069_mut, pos_069_aa = get_mut(ref_aligned, hit_aligned,  64,  69, 'M')
    pos_234_mut, pos_234_aa = get_mut(ref_aligned, hit_aligned, 229, 234, 'K')
    pos_235_mut, pos_235_aa = get_mut(ref_aligned, hit_aligned, 230, 235, 'T')
    if (pos_069_mut or pos_234_mut or pos_235_mut) and not bla_class.endswith('_inhR'):
        bla_class += '_inhR'
        class_changing_mutations += [pos_069_mut, pos_234_mut, pos_235_mut]

    # Mutations at these sites don't change the class, but will still be reported:
    pos_025_mut, pos_025_aa = get_mut(ref_aligned, hit_aligned,  20,  25, 'A')
    pos_035_mut, pos_035_aa = get_mut(ref_aligned, hit_aligned,  30,  35, 'L')
    pos_146_mut, pos_146_aa = get_mut(ref_aligned, hit_aligned, 141, 146, 'A')
    pos_156_mut, pos_156_aa = get_mut(ref_aligned, hit_aligned, 151, 156, 'G')
    pos_240_mut, pos_240_aa = get_mut(ref_aligned, hit_aligned, 234, 240, 'E')

    # Changes in the omega-loop will be reported, even if they are a deletion:
    pos_164_mut, pos_164_aa = get_mut(ref_aligned, hit_aligned, 159, 164, 'R')
    pos_165_mut, pos_165_aa = get_mut(ref_aligned, hit_aligned, 160, 165, 'W')
    pos_166_mut, pos_166_aa = get_mut(ref_aligned, hit_aligned, 161, 166, 'E')
    pos_167_mut, pos_167_aa = get_mut(ref_aligned, hit_aligned, 162, 167, 'T')
    pos_168_mut, pos_168_aa = get_mut(ref_aligned, hit_aligned, 163, 168, 'E')
    # pos_169_mut, pos_169_aa = get_mut(ref_aligned, hit_aligned, 164, 169, 'L')
    pos_170_mut, pos_170_aa = get_mut(ref_aligned, hit_aligned, 165, 170, 'N')
    pos_171_mut, pos_171_aa = get_mut(ref_aligned, hit_aligned, 166, 171, 'E')
    pos_172_mut, pos_172_aa = get_mut(ref_aligned, hit_aligned, 167, 172, 'A')
    pos_173_mut, pos_173_aa = get_mut(ref_aligned, hit_aligned, 168, 173, 'L')
    pos_174_mut, pos_174_aa = get_mut(ref_aligned, hit_aligned, 169, 174, 'P')
    pos_175_mut, pos_175_aa = get_mut(ref_aligned, hit_aligned, 170, 175, 'G')
    pos_176_mut, pos_176_aa = get_mut(ref_aligned, hit_aligned, 171, 176, 'D')
    pos_177_mut, pos_177_aa = get_mut(ref_aligned, hit_aligned, 172, 177, 'A')
    pos_178_mut, pos_178_aa = get_mut(ref_aligned, hit_aligned, 173, 178, 'R')
    # pos_179_mut, pos_179_aa = get_mut(ref_aligned, hit_aligned, 174, 179, 'D')

    omega_loop_seq = ''.join([pos_164_aa, pos_165_aa, pos_166_aa, pos_167_aa, pos_168_aa, pos_169_aa,
                          pos_170_aa, pos_171_aa, pos_172_aa, pos_173_aa, pos_174_aa, pos_175_aa,
                          pos_176_aa, pos_177_aa, pos_178_aa, pos_179_aa])
    if omega_loop_seq == 'RWETELNEALPGDARD':  # if it's the same as SHV-1
        omega_loop_seq = None

    shv_mutations = [pos_025_mut, pos_035_mut, pos_069_mut, pos_146_mut, pos_148_mut, pos_156_mut,
                     pos_169_mut, pos_179_mut, pos_234_mut, pos_235_mut, pos_238_mut, pos_240_mut]
    shv_mutations = [m for m in shv_mutations if m]
    class_changing_mutations = [m for m in class_changing_mutations if m]

    return bla_class, shv_mutations, class_changing_mutations, omega_loop_seq


def get_percent_identity(ref_aligned, hit_aligned):
    matches = 0
    for i, a in enumerate(ref_aligned):
        b = hit_aligned[i]
        if a == b:
            matches += 1
    return matches / len(ref_aligned)


def get_mut(ref_aligned, hit_aligned, ref_pos, ambler_pos, ref_aa):
    """
    ref_pos:    the index of the AA in SHV-1 (0-based because we're looking it up in Python)
    ambler_pos: the index of the AA in the Ambler alignment (1-based because it's just for the name)
    ref_aa:     the AA in the SHV-1 sequence
    """
    ref_no_gaps, hit_no_gaps = [], []
    for i, a in enumerate(ref_aligned):
        b = hit_aligned[i]
        if a != '-':
            ref_no_gaps.append(a)
            hit_no_gaps.append(b)
    assert len(ref_no_gaps) == 286
    assert ref_no_gaps[ref_pos] == ref_aa
    hit_aa = hit_no_gaps[ref_pos]
    if ref_aa != hit_aa and hit_aa != '-':
        mutation_notation = f'{ambler_pos}{hit_aa}'
    else:
        mutation_notation = ''
    return mutation_notation, hit_aa