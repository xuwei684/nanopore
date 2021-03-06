from nanopore.metaAnalyses.abstractMetaAnalysis import AbstractMetaAnalysis
import os, sys
import xml.etree.cElementTree as ET
from jobTree.src.bioio import system, fastqRead
from nanopore.analyses.utils import samIterator
import pysam

class Read():
    """stores a individual read and everything about it"""
    def __init__(self, name, seq, readType, readFastqFile, mapRefPairs):
        self.seq = seq
        self.name = name
        self.readType = readType
        self.readFastqFile = readFastqFile
        self.mapRefPairs = mapRefPairs

        if mapRefPairs is not None:
            self.is_mapped = True
            self.mappers, self.references = set(mapRefPairs[0]), set(mapRefPairs[1])
        else:
            self.is_mapped = False
            self.mappers, self.references = None, None

    def get_map_ref_pair(self):
        if self.mapRefPairs is not None:
            for mapper, reference in zip(self.mapRefPairs[0], self.mapRefPairs[1]):
                yield (mapper, reference)

class AbstractUnmappedMetaAnalysis(AbstractMetaAnalysis):
    """Builds a database of reads and the information gathered about them during analysis"""
    def __init__(self, outputDir, experiments):
        AbstractMetaAnalysis.__init__(self, outputDir, experiments)
        
        allReads = {(name, readFastqFile, readType, seq) for readFastqFile, readType, referenceFastaFile, mapper, analyses, resultsDir \
            in self.experiments for name, seq, qual in fastqRead(readFastqFile)}
        
        mappedReads = dict()
        for readFastqFile, readType, referenceFastaFile, mapper, analyses, resultsDir in self.experiments:
            for record in samIterator(pysam.Samfile(os.path.join(resultsDir, "mapping.sam"))):
                if not record.is_unmapped:
                    if (record.qname, readFastqFile) not in mappedReads:
                        mappedReads[(record.qname, readFastqFile)] = set()
                    mappedReads[(record.qname, readFastqFile)].add((mapper.__name__, referenceFastaFile))

        self.reads = list()
        for name, readFastqFile, readType, seq in allReads:
            if (name, readFastqFile) in mappedReads:
                mappers, referenceFastaFiles = map(tuple, zip(*mappedReads[(name, readFastqFile)]))
                self.reads.append(Read(name, seq, readType, readFastqFile, (mappers, referenceFastaFiles)))
            else:
                self.reads.append(Read(name, seq, readType, readFastqFile, None))
