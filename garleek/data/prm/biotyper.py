"""
Generate a Garleek --types file from TINKER PRM `biotype` definitions.

This script is only meant as first automatic attempt to provide 
atom types. Careful manual revision is encouraged!

.. todo::

    Provide PDB residue names for missing entries in AA dictionary
    (mainly nucleic acids)

"""

import re
import os
import sys


RESIDUES = {
    "3'-hydroxyl dna":              '',
    "3'-hydroxyl rna":              '',
    "3'-monophosphate op dna":      '',
    "3'-monophosphate op rna":      '',
    "3'-monophosphate os dna":      '',
    "3'-monophosphate os rna":      '',
    "3'-monophosphate p dna":       '',
    "3'-monophosphate p rna":       '',
    "5'-hydroxyl dna":              '',
    "5'-hydroxyl rna":              '',
    "5'-monophosphate op dna":      '',
    "5'-monophosphate op rna":      '',
    "5'-monophosphate os dna":      '',
    "5'-monophosphate os rna":      '',
    "5'-monophosphate p dna":       '',
    "5'-monophosphate p rna":       '',
    "acetyl n-terminus":            'NACE',
    "adenosine":                    '',
    "alanine":                      'ALA',
    "amide c-terminus":             '',
    "arginine":                     'ARG',
    "asparagine":                   'ASN',
    "aspartic acid":                'ASP',
    "aspartic acid (cooh)":         'ASH',
    "calcium ion":                  'CA',
    "chloride ion":                 'CL',
    "c-terminal aib":               'CAIB',
    "c-terminal ala":               'CALA',
    "c-terminal arg":               'CARG',
    "c-terminal ash (cooh)":        'CASH',
    "c-terminal asn":               'CASN',
    "c-terminal asp":               'CASP',
    "c-terminal cyd (s-)":          'CCYM',
    "c-terminal cys (sh)":          'CCYS',
    "c-terminal cyx (ss)":          'CCYX',
    "c-terminal glh (cooh)":        'CGLH',
    "c-terminal gln":               'CGLN',
    "c-terminal glu":               'CGLU',
    "c-terminal gly":               'CGLY',
    "c-terminal his (+)":           'CHIP',
    "c-terminal his (hd)":          'CHID',
    "c-terminal his (he)":          'CHIE',
    "c-terminal ile":               'CILE',
    "c-terminal leu":               'CLEU',
    "c-terminal lyd (nh2)":         'CLYN',
    "c-terminal lys":               'CLYS',
    "c-terminal met":               'CMET',
    "c-terminal orn":               'CORN',
    "c-terminal phe":               'CPHE',
    "c-terminal pro":               'CPRO',
    "c-terminal ser":               'CSER',
    "c-terminal thr":               'CTHR',
    "c-terminal trp":               'CTRP',
    "c-terminal tyd (o-)":          'CTYD',
    "c-terminal tyr":               'CTYR',
    "c-terminal val":               'CVAL',
    "cysteine (s-)":                'CYM',
    "cysteine (sh)":                'CYS',
    "cystine (ss)":                 'CYX',
    "cytidine":                     '',
    "deoxyadenosine":               '',
    "deoxycytidine":                '',
    "deoxyguanosine":               '',
    "deoxythymidine":               '',
    "deprotonated n-terminus":      '',
    "formyl n-terminus":            '',
    "glutamic acid":                'GLU',
    "glutamic acid (cooh)":         'GLH',
    "glutamine":                    'GLN',
    "glycine":                      'GLY',
    "guanosine":                    '',
    "histidine (+)":                'HIP',
    "histidine (hd)":               'HID',
    "histidine (he)":               'HIE',
    "isoleucine":                   'ILE',
    "leucine":                      'LEU',
    "lysine":                       'LYS',
    "lysine (nh2)":                 'LYN',
    "magnesium ion":                'MG',
    "methionine":                   'MET',
    "methylalanine (aib)":          'AIB',
    "n-meamide c-terminus":         '',
    "n-terminal aib":               'NAIB',
    "n-terminal ala":               'NALA',
    "n-terminal arg":               'NARG',
    "n-terminal ash (cooh)":        'NASH',
    "n-terminal asn":               'NASN',
    "n-terminal asp":               'NASP',
    "n-terminal cyd (s-)":          'NCYM',
    "n-terminal cys (sh)":          'NCYS',
    "n-terminal cyx (ss)":          'NCYX',
    "n-terminal glh (cooh)":        'NGLH',
    "n-terminal gln":               'NGLN',
    "n-terminal glu":               'NGLU',
    "n-terminal gly":               'NGLY',
    "n-terminal his (+)":           'NHIP',
    "n-terminal his (hd)":          'NHID',
    "n-terminal his (he)":          'NHIE',
    "n-terminal ile":               'NILE',
    "n-terminal leu":               'NLEU',
    "n-terminal lyd (nh2)":         'NLYN',
    "n-terminal lys":               'NLYS',
    "n-terminal met":               'NMET',
    "n-terminal orn":               'NORN',
    "n-terminal phe":               'NPHE',
    "n-terminal pro":               'NPRO',
    "n-terminal ser":               'NSER',
    "n-terminal thr":               'NTHR',
    "n-terminal trp":               'NTRP',
    "n-terminal tyd (o-)":          'NTYD',
    "n-terminal tyr":               'NTYR',
    "n-terminal val":               'NVAL',
    "ornithine":                    'ORN',
    "phenylalanine":                'PHE',
    "phosphodiester dna":           '',
    "phosphodiester rna":           '',
    "potassium ion":                'K',
    "proline":                      'PRO',
    "protonated c-terminus":        '',
    "pyroglutamic acid":            'GLP',
    "serine":                       'SER',
    "sodium ion":                   'NA',
    "threonine":                    'THR',
    "tryptophan":                   'TRP',
    "tyrosine":                     'TYR',
    "tyrosine (o-)":                'TYD',
    "uridine":                      '',
    "valine":                       'VAL',
    "water":                        'WAT',
}
ALIASES = {
    'OE': ('OE1', 'OE2'),
    'OD': ('OD1', 'OD2'),
    'NH': ('NH1', 'NH2'),
    'NE': ('NE2',),
    'ND': ('ND1',),
    'ND1': ('ND11', 'ND12'),
    'NE2': ('NE21',, 'NE22'),
    'HA': ('HA1', 'HA2', 'HA3'),
    'HB': ('HB1', 'HB2', 'HB3'),
    'HC': ('HC1', 'HC2', 'HC3'),
    'HD': ('HD1', 'HD2', 'HD3'),
    'HD1': ('HD11', 'HD12', 'HD13'),
    'HD2': ('HD21', 'HD22', 'HD23'),
    'HE': ('HE1', 'HE2', 'HE3'),
    'HE1': ('HE11', 'HE12'),
    'HE2': ('HE21', 'HE22'),
    'HG': ('HG1', 'HG2', 'HG3',),
    'HG1': ('HG11', 'HG12', 'HG13'),
    'HG2': ('HG21', 'HG22', 'HG23',),
    'HH': ('HH1', 'HH2', 'HH11', 'HH12', 'HH21', 'HH22'),
    'HH1': ('HH11', 'HH12'),
    'HH2': ('HH21', 'HH22'),
    'HZ': ('HZ1', 'HZ2', 'HZ3'),
    'CE': ('CE1', 'CE2'),
    'CD': ('CD1', 'CD2'),
    'HN': ('H'),  # check
    'OXT': ('O'), # check
    'H': ('H1', 'H2'),
}

def main(prm_file):
    biotype_rx = r'^biotype\s+\d+\s+(\S+)\s+"(.*)"\s+([\-\d]+)'
    d = {
    }
    with open(prm_file) as f:
        for line in f:
            search = re.search(biotype_rx, line)
            if search:
                atom_type, residue_str, tinker_type = search.groups()
                residue_str = residue_str.lower()
                if residue_str in RESIDUES:
                    restype = RESIDUES[residue_str].upper()
                    if restype:
                        d[restype + '_' + atom_type] = tinker_type
                        for alias in ALIASES.get(atom_type, ''):
                            d[restype + '_' + alias] = tinker_type
    return d

if __name__ == '__main__':
    try:
        d = main(sys.argv[1])
    except IndexError:
        sys.exit('Usage: biotyper.py forcefield.prm output.types')
    else:
        print('\n'.join('{} {}'.format(k, v) for (k,v) in sorted(d.items())))
