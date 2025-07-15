clear
clc

addpath(genpath('~/GIT_projects/Github/sparse-grids-matlab-kit/'));
addpath(genpath('~/GIT_projects/Github/umbridge/matlab/'));

uri = 'http://0.0.0.0:4242';  

model = HTTPModel(uri,'forward');
f = @(y) model.evaluate([y(1) 10^(y(2))]');


beta_min = 10;
beta_max = 89.99;
logc_min = -8;
logc_max = 1;
domain = [beta_min logc_min
          beta_max logc_max];
      
knots_beta = @(n) knots_CC(n,beta_min,beta_max);
knots_logc = @(n) knots_CC(n,logc_min,logc_max);


N = 2;
w = 4;
[S,C] = create_sparse_grid(N,w,{knots_beta, knots_logc},@lev2knots_doubling);
Sr = reduce_sparse_grid(S);

tic
f_values = evaluate_on_sparse_grid(f,Sr);
toc


plot_sparse_grids_interpolant(S,Sr,domain,f_values,'with_f_values');


sample_size = 1000;
M = get_interval_map(domain(1,:),domain(2,:),'uniform');
MC_sample = M(rand(N,sample_size)*2-1);

% plot_sparse_grid(asreduced(MC_sample));

MC_values = interpolate_on_sparse_grid(S,Sr,f_values,MC_sample);

figure
histogram(MC_values,'Normalization','pdf');

Prob_Fos_below_1 =length(find(MC_values<1))/sample_size;
