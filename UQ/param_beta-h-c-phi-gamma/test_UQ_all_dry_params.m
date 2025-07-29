% prior to this, run server as: python3 bishop_beta_c.py

clear
clc

addpath(genpath('~/GIT_projects/Github/sparse-grids-matlab-kit/'));
addpath(genpath('~/GIT_projects/Github/umbridge/matlab/'));

uri = 'http://0.0.0.0:4242';  

model = HTTPModel(uri,'forward');


%f = @(y) model.evaluate([y(1) y(2) y(3) 20 20]);
f = @(y) model.evaluate(y);

N = 5;

beta_min = 10;
beta_max = 89.99;
h_min = 1;
h_max = 20;
c_min = 0.00001;
c_max = 1000;
phi_min = 0;
phi_max = 40;
gamma_min = 15;
gamma_max = 25;
domain = [beta_min h_min c_min phi_min gamma_min
          beta_max h_max c_max phi_max gamma_max];
      
knots_beta = @(n) knots_CC(n,beta_min,beta_max);
knots_h = @(n) knots_CC(n,h_min,h_max);
knots_c = @(n) knots_CC(n,c_min,c_max);
knots_phi = @(n) knots_CC(n,phi_min,phi_max);
knots_gamma = @(n) knots_CC(n,gamma_min,gamma_max);


%% a-priori sparse grid
% w = 3;
% [S,C] = create_sparse_grid(N,w,{knots_beta, knots_h, knots_c},@lev2knots_doubling);
% %[S,C] = create_sparse_grid(N,w,{knots_beta, knots_h, knots_c, knots_phi, knots_gamma},@lev2knots_doubling);
% Sr = reduce_sparse_grid(S);
% 
% disp(Sr.size)
% %plot_sparse_grid(S,[2 5])
% 
% tic
% f_values = evaluate_on_sparse_grid(f,Sr);
% toc

%% 
controls = struct('nested',true,'max_pts',100);
adapted = adapt_sparse_grid(f,N,{knots_beta, knots_h, knots_c, knots_phi, knots_gamma},@lev2knots_doubling,[],controls)
 


%%
% plot_sparse_grids_interpolant(S,Sr,domain,f_values,'two_dim_cuts',[1 3]);

% plot_sparse_grids_interpolant(S,Sr,domain(:,1:3),f_values,'two_dim_cuts',[1 3]);

% plot_sparse_grids_interpolant(S,Sr,[beta_min, c_min; beta_max, c_max],f_values);

%%
nb_c_vals = 20;
oones = ones(1,nb_c_vals);
sample_c = linspace(c_min,c_max,nb_c_vals);
beta_fix = 30;
h_fix = 3;
phi_fix = 30;
gamma_fix = 20;
 
sample = [beta_fix*oones;
          h_fix*oones;
          sample_c;
          phi_fix*oones;
          gamma_fix*oones];

% sample = [  beta_fix*oones;
%             h_fix*oones;
%             sample_c];


fos_values_vs_c = interpolate_on_sparse_grid(adapted.S,adapted.Sr,adapted.f_on_Sr,sample);

true_values = zeros(1,nb_c_vals);    
for i = 1:nb_c_vals
    true_values(i) = f([beta_fix h_fix sample_c(i) phi_fix gamma_fix]);
end

plot(sample_c,fos_values_vs_c,'-o')
hold on
plot(sample_c,true_values,'-x')


%%


sample_size = 1000;
% M = get_interval_map(domain(1,:),domain(2,:),'uniform');
% MC_sample = M(rand(N,sample_size)*2-1);

beta_meas =  30;
beta_st_dev = 2;

logc_meas = -4;
logc_st_dev = 0.1;

MC_sample = [randn(1,sample_size)*beta_st_dev + beta_meas;
             randn(1,sample_size)*logc_st_dev + logc_meas;];

plot_sparse_grid(asreduced(MC_sample));

MC_values = interpolate_on_sparse_grid(S,Sr,f_values,MC_sample);

figure
histogram(MC_values,'Normalization','pdf');

Prob_Fos_below_1 =length(find(MC_values<1))/sample_size;
