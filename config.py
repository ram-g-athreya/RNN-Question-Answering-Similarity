import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description='PyTorch TreeLSTM for Sentence Similarity on Dependency Trees')
    # data arguments
    parser.add_argument('--data', default='data/lc-quad/',
                        help='path to dataset')
    parser.add_argument('--save', default='checkpoints/',
                        help='directory to save checkpoints in')
    parser.add_argument('--expname', type=str, default='rnn-question-answering-similarity',
                        help='Name to identify experiment')
    # model arguments
    parser.add_argument('--mem_dim', default=150, type=int,
                        help='Size of TreeLSTM cell state')
    parser.add_argument('--hidden_dim', default=50, type=int,
                        help='Size of classifier MLP')
    parser.add_argument('--freeze_embed', action='store_true',
                        help='Freeze word embeddings')
    # training arguments
    parser.add_argument('--epochs', default=3, type=int,
                        help='number of total epochs to run')
    parser.add_argument('--batchsize', default=25, type=int,
                        help='batchsize for optimizer updates')
    parser.add_argument('--lr', default=1e-2, type=float,
                        metavar='LR', help='initial learning rate')
    parser.add_argument('--wd', default=1e-4, type=float,
                        help='weight decay (default: 1e-4)')
    parser.add_argument('--emblr', default=1e-2, type=float,
                        metavar='EMLR', help='initial embedding learning rate')
    parser.add_argument('--sparse', action='store_true',
                        help='Enable sparsity for embeddings, \
                              incompatible with weight decay')
    parser.add_argument('--optim', default='adagrad',
                        help='optimizer (default: adagrad)')

    # miscellaneous options
    parser.add_argument('--seed', default=42, type=int,
                        help='random seed (default: 42)')
    cuda_parser = parser.add_mutually_exclusive_group(required=False)
    cuda_parser.add_argument('--cuda', dest='cuda', action='store_true')
    cuda_parser.add_argument('--no-cuda', dest='cuda', action='store_false')
    parser.set_defaults(cuda=True)

    args = parser.parse_args()
    return args
