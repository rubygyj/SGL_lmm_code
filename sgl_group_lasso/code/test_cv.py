"""
"""

import csv
import scipy as SP
import scipy.linalg as LA
import pdb
import lmm_lasso_pg as lmm_lasso
import os
import sys

if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.stderr.write('\tUsage: python test_cv.py [ypheno.csv]\n');
        sys.exit(1);

    root = 'data'
    gene_file = os.path.join(root, 'gene_chr1.csv')
    ypheno_file = os.path.join(root, 'pheno', sys.argv[1])
    kinship_file = os.path.join(root, 'kinship_x.csv')
    group_file = os.path.join(root, 'simu_chr1_group_stru_01.csv')
    
    # load genotypes
    X = SP.array(list(csv.reader(open(gene_file,'rb'),
                                 delimiter=','))).astype(float)
    [n_f, n_s] = X.shape
    
    for i in xrange(n_f):
        m=X[i].mean()
        std=X[i].std()
        X[i]=(X[i]-m)/std
    X = X.T
    
    # simulate phenotype
    y = SP.array(list(csv.reader(open(ypheno_file, 'rb'),
                                delimiter=','))).astype(float) 

    
    # init
    debug = False
    n_train = int(n_s*0.7)
    n_test = n_s - n_train
    n_reps = 10
    f_subset = 0.7
    
    muinit = 0.1
    mu2init = 0.1
    ps_step = 3
    
        
    # split into training and testing
    train_idx = SP.random.permutation(SP.arange(n_s))
    test_idx = train_idx[n_train:]
    train_idx = train_idx[:n_train]
    
    # calculate kernel
    # the first 2622 SNP are in the first chromosome which we are testing
    XO = SP.array(list(csv.reader(open(kinship_file, 'rb'),
                                delimiter=','))).astype(float) 
    K = 1./XO.shape[0]*SP.dot(XO.T,XO)

    group = SP.array(list(csv.reader(open(group_file, 'rb'),
                                delimiter=','))).astype(int)
    group = SP.squeeze(group, axis=1)
    idx = 0
    gp = list()
    for i in range(len(group)):
        gp.append( [idx, idx+group[i]] )
        idx += group[i]
    group = gp
    
    # Glasso Parameter selection by 5 fold cv
    optmu=muinit
    optmu2=mu2init
    optcor=0
    for j1 in range(7):
        for j2 in range(7):
            mu=muinit*(ps_step**j1)
            mu2=mu2init*(ps_step**j2)
            cor=0
            for k in range(5): #5 for full 5 fold CV
                train1_idx=SP.concatenate((train_idx[:int(n_train*k*0.2)],train_idx[int(n_train*(k+1)*0.2):n_train]))
                valid_idx=train_idx[int(n_train*k*0.2):int(n_train*(k+1)*0.2)]
                res1=lmm_lasso.train(X[train1_idx],K[train1_idx][:,train1_idx],y[train1_idx],mu,mu2,group)
                w1=res1['weights']
                yhat = lmm_lasso.predict(y[train1_idx],X[train1_idx,:],X[valid_idx,:],K[train1_idx][:,train1_idx],K[valid_idx][:,train1_idx],res1['ldelta0'],w1)
                cor += SP.dot(yhat.T-yhat.mean(),y[valid_idx]-y[valid_idx].mean())/(yhat.std()*y[valid_idx].std())
            
            print mu, mu2, cor[0,0]
            if cor>optcor:
                optcor=cor
                optmu=mu
                optmu2=mu2
                
    print optmu, optmu2, optcor[0,0]
    
    # train
    res = lmm_lasso.train(X[train_idx],K[train_idx][:,train_idx],y[train_idx],optmu,optmu2,group)
    w = res['weights']
        
    # predict
    ldelta0 = res['ldelta0']
    yhat = lmm_lasso.predict(y[train_idx],X[train_idx,:],X[test_idx,:],K[train_idx][:,train_idx],K[test_idx][:,train_idx],ldelta0,w)
    corr = 1./n_test * SP.dot(yhat.T-yhat.mean(),y[test_idx]-y[test_idx].mean())/(yhat.std()*y[test_idx].std())
    print corr[0,0]
    
    # lasso parameter selection by 5 fold cv
    optmu0=muinit
    optcor=0
    for j1 in range(7):
        mu=muinit*(ps_step**j1)
        cor=0
        for k in range(5):
            train1_idx=SP.concatenate((train_idx[:int(n_train*k*0.2)],
                                       train_idx[int(n_train*(k+1)*0.2):n_train]))
            valid_idx=train_idx[int(n_train*k*0.2):int(n_train*(k+1)*0.2)]
            res1=lmm_lasso.train(X[train1_idx],K[train1_idx][:,train1_idx],y[train1_idx],mu,0,[])
            w1=res1['weights']
            yhat = lmm_lasso.predict(y[train1_idx],X[train1_idx,:],X[valid_idx,:],K[train1_idx][:,train1_idx],K[valid_idx][:,train1_idx],res1['ldelta0'],w1)
            cor += SP.dot(yhat.T-yhat.mean(),y[valid_idx]-y[valid_idx].mean())/(yhat.std()*y[valid_idx].std())
        
        print mu, cor[0,0]
        if cor>optcor:
            optcor=cor
            optmu0=mu
                
    print optmu0, optcor[0,0]
    
    # train
    res = lmm_lasso.train(X[train_idx],K[train_idx][:,train_idx],y[train_idx],optmu0,0,[])
    w=res['weights']
       
    # predict
    ldelta0 = res['ldelta0']
    yhat = lmm_lasso.predict(y[train_idx],X[train_idx,:],X[test_idx,:],K[train_idx][:,train_idx],K[test_idx][:,train_idx],ldelta0,w)
    corr = 1./n_test * SP.dot(yhat.T-yhat.mean(),y[test_idx]-y[test_idx].mean())/(yhat.std()*y[test_idx].std())
    print corr[0,0]    
    
    
    # stability selection
    # group info included
    ss = lmm_lasso.stability_selection(X,K,y,optmu,optmu2,group,n_reps,f_subset)
    
    sserr1=0
    sserr2=0
    for i in range(n_f):
        if i in idx:
            if ss[i]<n_reps*0.8:
                sserr1+=1
        else:
            if ss[i]>=n_reps*0.8:
                sserr2+=1
                
    # group info not included
    ss2=lmm_lasso.stability_selection(X,K,y,optmu0,0,[],n_reps,f_subset)
    
    ss2err1=0
    ss2err2=0
    for i in range(n_f):
        if i in idx:
            if ss2[i]<n_reps*0.7:
                ss2err1+=1
        else:
            if ss2[i]>=n_reps*0.7:
                ss2err2+=1
    
    # Output
    
    for i in range(n_f):
        print i, (i in idx), ss[i], ss2[i]
    
    print optmu,optmu2,optmu0
    print sserr1, sserr2, ss2err1, ss2err2
