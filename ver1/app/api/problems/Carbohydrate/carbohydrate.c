#include <stdio.h>
#include <string.h>

int stack[1024] ;
int top = 0 ;

int
weight (char * f) 
{
	int i ; 
	int summ = 0 ;
	int last = 0 ; 

	for (i = 0 ; i < strlen(f) ; i++) {
		switch (f[i]) {
			case 'H': {
				summ += 1 ;
				last = 1 ; 
				break ;
			}

			case 'C': {
				summ += 12 ;
				last = 12 ;
				break ;
			}

			case 'O': {
				summ += 16 ;
				last = 16 ;
				break ;
			}

			case '(': {
				stack[top++] = summ ;
				summ = 0 ;			
				break ;
			}

			case ')': {
				last = summ ;				
				summ = stack[--top] ;
				summ += last ;
				break ;
			}

			default : /* isdigit(f[i]) */ {
				int num = f[i] - '0' ; 
				summ += last * (num - 1) ;
				break ;
			}
		}
	}
	return summ ; 
}

int 
main ()
{
	char s[1024] ;

	scanf("%s", s) ;
	printf("%d\n", weight(s)) ;
}
