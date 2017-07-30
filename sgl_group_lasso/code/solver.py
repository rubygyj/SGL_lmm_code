from commands import getoutput as go
import threading
import argparse
import os
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--algo', '-a', default = 'test_cv_0.py', help = 'the python file with algorithm, default is test_cv_0.py')
    parser.add_argument('--dir', '-d', default = 'data/pheno', help = 'the root path of the ypheno files, default is data/pheno/')
    parser.add_argument('--use-group-lasso', '-g', default = 'true', help = 'whether use group lasso, default is true, value is true/false')
    parser.add_argument('--use-lasso', '-l', default = 'true', help = 'whether use lasso, default is true, value is true/false')
    args = parser.parse_args()

    for ypheno_root, ypheno_dirs, files in os.walk(args.dir, topdown=False):
        for ypheno_file_name in files:
            if ypheno_file_name[-10:-4] != 'result' and ypheno_file_name[-4:] == '.csv':
                root = ypheno_root[5:]
                file = os.path.join(root, ypheno_file_name)

                t = go('python {0} {1} {2} {3}'.format(
                                         args.algo, file, args.use_group_lasso, args.use_lasso))
                print 'Current command: python {0} {1} {2} {3}.'.format(
                                         args.algo, file, args.use_group_lasso, args.use_lasso)
                print '-------- Results --------'
                print t
                print '-------------------------'

                status_file = '{0}_{1}_status.log'.format(args.algo.replace('.py', ''), ypheno_file_name.replace('.csv', ''))
                status = open(status_file, 'w')
                status.writelines(t)
                status.close()
    print "all over %s" % time.ctime()
