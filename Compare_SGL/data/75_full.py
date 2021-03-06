#Normalize genotype and combine it with fake phenotype

import csv
import numpy as NP
import scipy as SP
import pdb
import os
import lmm_lasso
from datetime import datetime

def normalize(l):
    count={'A':0,'T':0,'G':0,'C':0}
    for c in l:
        count[c]+=1
    dft=max(count,key=count.get)
    arr = SP.array(l!=dft, SP.float32)
    return (arr-arr.mean())/arr.std(), arr.mean()

if __name__ == "__main__":

    # load genotypes
    genofile = open('simu_chr2_5.csv','rb')
    genoreader = csv.reader(genofile, delimiter=',')
    X0 = SP.array(list(genoreader))
    
    # remove incomplete lines
    X=(X0[0:2]).tolist()
    for i in xrange(2,X0.shape[0]):
        X.append(X0[i])
#        if SP.rand()<0.05 and not('-' in X0[i]):
#            X.append(X0[i])
            
    # load leaf number phenotype
    X1 = SP.genfromtxt('ln10.tsv', delimiter='\t',dtype=str)
    pos2pheno = dict(zip(X1[:,0], X1[:,1]))
    pheno = [X[1][0], X[1][1]]+[int(pos2pheno[p])\
            if p in pos2pheno else 0 for p in X[1][2:]]

    #normalize and output genotype            
    Y=[pheno[2:]]
    for i in xrange(2,len(X)):
        v, a=normalize(X[i][2:])
        if a>0.05:
            Y.append(v)

    with open("genotype75.csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(Y[1:])
    nf=len(Y)-1
    print nf

    #obtain genotype & phenotype for samples with complete phenotype
    MY=SP.array(Y).transpose()
    RMY=MY[MY[:,0]>0]
    RY=RMY[:,0]
    RY=(RY-RY.mean())/RY.std()
    RX=RMY[:,1:]

    #train null model for these samples
    COR=1./nf*SP.dot(RX,RX.transpose())

    FX=MY[:,1:]
    FCOR=1./nf*SP.dot(FX,FX.transpose())

    threshold = 1e-4 
    min_delta = 100
    for i in xrange(10000):
        res=lmm_lasso.train_nullmodel(RY,COR)
        delta=SP.exp(res[2])
        delta1 = delta
    
        #get fake phenotype
        D=SP.diag(SP.array([delta]*len(Y[1])))
        FY=SP.random.multivariate_normal(SP.array([0]*len(Y[1])),SP.add(FCOR,D))
        FY=(FY-FY.mean())/FY.std()
        FY=SP.array([FY])
    
        #validate fake phenotype, that it has similar delta as we start with
        res=lmm_lasso.train_nullmodel(FY.transpose(),FCOR)
        delta=SP.exp(res[2])
        dd = abs(delta - delta1)
        if dd < min_delta: min_delta = dd
        #if i % 100 == 0: 
        print('{} [try {}] current delta: {:.6f} minimum delta: {:.6f} '.format(datetime.now(),i,dd,min_delta))
        print('\tdelta = {}, fdelta = {}'.format(delta1, delta))        
        if dd < threshold: 
            with open("phenotype75.csv", "wb") as f:
                writer = csv.writer(f)
                writer.writerows(FY.transpose())
            break

    #results when running all: 200155
    #0.20729029054
    #0.334130189795

