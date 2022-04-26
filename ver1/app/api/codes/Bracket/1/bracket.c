#include <stdio.h>

int
main () 
{
	int maxdepth = 0 ; 

	char st[100] ;
	int top = 0 ;

	char t[101] ;


	scanf("%s", t) ;

	int i ;
	for (i = 0 ; t[i] != 0x0 ; i++) {
		switch (t[i]) {
			case '(':
			case '<':
			case '{':
			case '[':
				st[top++] = t[i] ;
				maxdepth = (top > maxdepth) ? top : maxdepth ;
				break ; 

			case ')':
			case '>':
			case '}':
			case ']':
				if (top > 0) {					
					if ((st[top-1] == '(' && t[i] == ')') || 
					   	(st[top-1] == '<' && t[i] == '>') || 
					  	(st[top-1] == '{' && t[i] == '}') || 
						(st[top-1] == '[' && t[i] == ']')) {
						top-- ;
					}
					else {
						printf("1") ; return 0 ;
					}
				}
				else {
					printf("1") ; return 0 ;
				}
				break ;
		}
	}
	if (top != 0) {
		printf("1") ;
	}
	else {
		printf("%d", maxdepth) ;
	}
	return 0 ;
}
