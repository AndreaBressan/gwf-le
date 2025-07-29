
clear
clc

addpath(genpath('~/GIT_projects/Github/sparse-grids-matlab-kit/'));
addpath(genpath('~/GIT_projects/Github/umbridge/matlab/'));

uri = 'http://0.0.0.0:4242';  

model = HTTPModel(uri,'forward');


% compact parameter M = c/(gamma*H*tan(phi)) => c = M*gamma*H*tan(phi);
h0 = 1;
gamma0 = 1;
phi0 = 1; 

f = @(y) model.evaluate([y(1) h0 y(2)*gamma0*h0*tan(deg2rad(phi0)) phi0 gamma0]);

N = 2;

beta_min = 10;
beta_max = 89.99;
% compact parameter M = c/(gamma*H*tan(phi))
% h_min = 1;
% h_max = 20;
% c_min = 0.00001;
% c_max = 1000;
% phi_min = 0;
% phi_max = 40;
% gamma_min = 15;
% gamma_max = 25;
M_min = 0;
M_max = 10;

domain = [beta_min M_min
          beta_max M_max];
      
knots_beta = @(n) knots_CC(n,beta_min,beta_max);
knots_M = @(n) knots_CC(n,M_min,M_max);


w = 3;
[S,C] = create_sparse_grid(N,w,{knots_beta, knots_M},@lev2knots_doubling);
Sr = reduce_sparse_grid(S);
disp(Sr.size)

tic
f_values = evaluate_on_sparse_grid(f,Sr);
toc


%%
nb_M_vals = 20;
oones = ones(1,nb_M_vals);
beta_fix = 30;
sample_M = linspace(M_min,M_max,nb_M_vals);


sample = [beta_fix*oones;
          sample_M];

fos_values_vs_M = interpolate_on_sparse_grid(S,Sr,f_values,sample);

true_values = zeros(1,nb_M_vals);    
for i = 1:nb_M_vals
    true_values(i) = f([beta_fix sample_M(i)]);
end

plot(sample_M,fos_values_vs_M,'-o','DisplayName','modello surrogato')
hold on
plot(sample_M,true_values,'-x','DisplayName','valori veri')

legend show