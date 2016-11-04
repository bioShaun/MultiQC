#!/usr/bin/env python

""" MultiQC module to parse output from Prokka """

from __future__ import print_function
from collections import OrderedDict
import json
import logging
import os
import re
from operator import itemgetter

from multiqc import config, BaseMultiqcModule, plots

# Initialise the logger
log = logging.getLogger(__name__)

class MultiqcModule(BaseMultiqcModule):

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Prokka', anchor='prokka',
        href='http://www.vicbioinformatics.com/software.prokka.shtml', 
        info="is a software tool for the rapid annotation of prokaryotic genomes.")
        
        # Parse logs
        self.prokka = dict()
        for f in self.find_log_files(config.sp['prokka'], filehandles=True):
            self.parse_prokka(f)

        if len(self.prokka) == 0:
            log.debug("Could not find any Prokka data in {}".format(config.analysis_dir))
            raise UserWarning
        
        log.info("Found {} logs".format(len(self.prokka)))
        self.write_data_file(self.prokka, 'multiqc_prokka')
        
        # Add Prokka's annotation stats to the general stats table
        headers = OrderedDict()
        headers['organism'] = {
            'title': 'Organism',
            'description': 'Organism',
        }
        #headers['contigs'] = {
        #    'title': 'Contigs',
        #    'description': 'Number of contigs',
        #    "min": 0,
        #}
        headers['bases'] = {
            'title': 'Bases',
            'description': 'Number of bases',
            "min": 0,
            'format': '{:i}%'
        }
        headers['CDS'] = {
            'title': 'CDS',
            'description': 'Number of CDS',
            "min": 0,
            'format': '{:i}%'
        }
        headers['tRNA'] = {
            'title': 'tRNA',
            'description': 'Number of tRNA',
            "min": 0,
            'format': '{:i}%'
        }
        headers['rRNA'] = {
            'title': 'rRNA',
            'description': 'Number of rRNA',
            "min": 0,
            'format': '{:i}%'
        }
        headers['tmRNA'] = {
            'title': 'tmRNA',
            'description': 'Number of tmRNA',
            "min": 0,
            'format': '{:i}%'
        }
        headers['sig_peptide'] = {
            'title': 'sig_peptide',
            'description': 'Number of sig_peptide',
            "min": 0,
            'format': '{:i}%'
        }
        self.general_stats_addcols(self.prokka, headers)
        
        # Make summary barplot
        # The stacked barplot is not really useful for Prokka
        self.intro += self.prokka_barplot()
        
    def parse_prokka(self, f):
        """ Parse prokka txt summary files. 
        
        Prokka summary files are difficult to identify as there are practically
        no distinct prokka identifiers in the filenames or file contents. This
        parser makes an attempt using the organism line, expected to be the
        first line of the file. 
        """

        s_name = None

        # Look at the first three lines, they are always the same
        first_line = f['f'].readline()
        contigs_line = f['f'].readline()
        bases_line = f['f'].readline()
        # If any of these fail, it's probably not a prokka summary file
        if not all((first_line.startswith("organism:"), 
                   contigs_line.startswith("contigs:"),
                   bases_line.startswith("bases:"))):
            return
        log.debug("%s appears to be a prokka summary file.", f['f'].name)

        # Get organism and sample name from the first line
        organism = " ".join(first_line.strip().split(":", maxsplit=1)[1].split()[:2])
        s_name = " ".join(first_line.split()[3:])
        self.prokka[s_name] = dict()
        self.prokka[s_name]['organism'] = organism
        log.debug("Found sample name '%s' for organism '%s'", s_name, organism)
        self.prokka[s_name]['contigs'] = int(contigs_line.split(":")[1])
        self.prokka[s_name]['bases'] = int(bases_line.split(":")[1])

        # Get additional info from remaining lines
        for line in f['f']:
            description, value = line.split(":")
            try:
                self.prokka[s_name][description] = int(value)
            except ValueError:
                log.debug("Unable to parse line: '%s'", line)

    
    def prokka_barplot (self):
        """ Make basic plot of the annotation stats """
        
        # Specify the order of the different possible categories
        keys = OrderedDict()
        #keys['contigs'] =       { 'color': '#437bb1', 'name': 'Contigs' }
        #keys['bases'] =         { 'color': '#437bb1', 'name': 'Bases' }
        keys['CDS'] =           { 'name': 'CDS' }
        keys['rRNA'] =          { 'name': 'rRNA' }
        keys['tRNA'] =          { 'name': 'tRNA' }
        keys['tmRNA'] =         { 'name': 'tmRNA' }
        keys['misc_RNA'] =      { 'name': 'misc RNA' }
        keys['sig_peptide'] =   { 'name': 'Signaling peptides' }
        
        # Config for the plot
        pconfig = {
            'id': 'prokka_plot',
            'title': 'Prokka',
            'ylab': '# Counts',
            'cpswitch_counts_label': 'Features'
        }
        
        return plots.bargraph.plot(self.prokka, keys, pconfig)
