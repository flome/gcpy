#include <math.h>
#include <stdlib.h>
#include <stdio.h>

double * kitis2006(int lenx, double *T, double *par){
   
    // read values from parameter array
    double Tm = par[0];
    double Im = par[1];
    double E = par[2];
    double Tg = par[3];  

    // allocate and initialize I pointer
    double *I;
    I = malloc(lenx*sizeof(double));

     // define constants
    double k = 8.61733e-05;

    // define criteria vars
    int z,l,n;
    double nFak;
    double B,D,Z,Z2,ZM,Z2M;
  	
    // Zm term
    int zM = abs(roundf(E*(Tm-Tg)/(k*Tm*Tg)));

    // loop over temperature values
	int i;
	for(i=0; i<lenx; i++){

		z = abs(roundf(E/k*(T[i]-Tg)/(T[i]*Tg)));
		if(z > 10){

			Z = 0;
			for(n=0; n<=z; n++){
				nFak = 1;
				for(l=1;l<=n;l++){
					nFak *= l;
				}
				Z += pow(-1,n)*nFak*pow(k*T[i]/E,n)*(pow(Tg/(Tg-T[i]),n+1)-1);	
			}
			// correction term
			Z += 0.5*pow(-1,z+1)*nFak*(z+1)*pow(k*T[i]/E,z+1)*(pow(Tg/(Tg-T[i]),z+2)-1);

			ZM = 0;
			for(n=0; n<=zM; n++){
				nFak = 1;
				for(l=1;l<=n;l++){
					nFak *= l;
				}
				ZM += pow(-1,n)*nFak*pow(k*Tm/E,n)*(pow(Tg/(Tg-Tm),n+1)-1);
			}
			// correction term
			ZM += 0.5*pow(-1,zM+1)*nFak*(zM+1)*pow(k*Tm/E,zM+1)*(pow(Tg/(Tg-Tm),zM+2)-1);

			I[i] = Im*exp(-1*E*(Tm-T[i])/(k*T[i]*Tm)+(Tg-Tm)/Tm*(ZM-T[i]/Tm*exp(-1*E*(Tm-T[i])/(k*T[i]*Tm))*Z));
		
		}else{

			B = E/(k*T[i])*(T[i]-Tg)/Tg;
			D = k*T[i]/E;

			Z = 0.5772156649+log(fabs(B));
			ZM = 0.5772156649+log(fabs(E/(k*Tm)*(Tm-Tg)/Tg));

			for(n=1; n<=50; n++){
				nFak = 1;
				for(l=1;l<=n;l++){
					nFak *= l;
				}
				Z += pow(B,n)/(n*nFak);
				ZM += pow(E/(k*Tm)*(Tm-Tg)/Tg,n)/(n*nFak);
			}
			
			Z2 = 0;
			for(n=0; n<=z; n++){
				nFak = 1;
				for(l=1;l<=n;l++){
					nFak *= l;
				}
				Z2 += pow(-1,n)*nFak*pow(D,n);
			}
			// correction term
			Z2 += 0.5*pow(-1,z+1)*nFak*(z+1)*pow(D,z+1);

			Z2M = 0;
			for(n=0; n<=zM; n++){
				nFak = 1;
				for(l=1;l<=n;l++){
					nFak *= l;
				}
				Z2M += pow(-1,n)*nFak*pow(k*Tm/E,n);
			}
			// correction term
			Z2M += 0.5*pow(-1,zM+1)*nFak*(zM+1)*pow(k*Tm/E,zM+1);

			// integral computation
			I[i] = Im*exp(-1*E*(Tm-T[i])/(k*T[i]*Tm)-E*(Tg-Tm)/(k*Tm*Tm)*exp(E*(Tg-Tm)/(k*Tm*Tg))*(ZM-Z)-(Tg-Tm)/Tm*(Z2M-Z2*T[i]/Tm*exp(-E*(Tm-T[i])/(k*T[i]*Tm))));
		}
	}

	return I;
}
