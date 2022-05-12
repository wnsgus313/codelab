#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef 
	struct {
		void * buffer ;
		int unit ;
		int capacity ;
		int top ;
	} 
	stack ;

stack * 
create_stack (int capacity, int unit) ;

void
delete_stack (stack * stack) ;

int 
push (stack * stack, void * elem) ;

int
pop (stack * stack, void * elem) ;

int 
is_empty (stack * stack) ;

int 
is_full (stack * stack) ;

int
get_size (stack * stack) ;

int
get_element (stack * stack, int index, void * elem) ;

int
main () 
{
	int n_tokens ;
	int i ; 
	stack * st ;

	st = create_stack(100, sizeof(int)) ;

	char buf[16] ;

	do {
		scanf("%s", buf) ;

		if (buf[0] == ';')
			break ;

		if (isdigit(buf[0])) {
			int val = atoi(buf) ;
			push(st, &val) ;
		}
		else {
			int val1, val2, ret ;
			switch (buf[0]) {
				case '~':
					pop(st, &val1) ;
					ret = val1 * -1 ;
					push(st, &ret) ;
					break ;

				case '+': 
					pop(st, &val2) ;
					pop(st, &val1) ;
					ret = val1 + val2 ;
					push(st, &ret) ;
					break ;

				case '-': 
					pop(st, &val2) ;
					pop(st, &val1) ;
					ret = val1 - val2 ;
					push(st, &ret) ;
					break ;

				case '*': 
					pop(st, &val2) ;
					pop(st, &val1) ;
					ret = val1 * val2 ;
					push(st, &ret) ;
					break ;

				case '/': 
					pop(st, &val2) ;
					pop(st, &val1) ;
					if (val2 == 0) {
						printf("undefined") ;
						exit(0) ;
					}
					ret = val1 / val2 ;
					push(st, &ret) ;
					break ;

				case '^':
					pop(st, &val2) ;
					pop(st, &val1) ;
					if (val2 < 0) {
						printf("undefined") ;
						exit(0) ;
					}

					ret = 1 ;
					while (val2 > 0) {
						ret *= val1 ;
						val2 -= 1 ;
					}					
					push(st, &ret) ;
					break ;					

				default:
					printf("invalid") ;
					exit(0) ;	
			}
		}
	} while (buf[0] != ';') ;

	if (get_size(st) > 1) {
		printf("invalid") ;
		exit(0) ;
	}

	int result ;
	pop(st, &result) ;
	printf("%d\n", result) ;

	delete_stack(st) ;
}

stack * 
create_stack (int capacity, int unit) 
{
	stack * st = malloc(sizeof(stack)) ;
	st->capacity = capacity ;
	st->unit = unit ;
	st->top = 0 ;
	st->buffer = calloc(capacity, unit) ;
	return st ;
}

void
delete_stack (stack * st) 
{
	if (st->buffer != 0x0)
		free(st->buffer) ;
	free(st) ;
}

int 
push (stack * st, void * elem)
{
	if (is_full(st))
		return 1 ;

	memcpy(st->buffer + ((st->top) * (st->unit)), elem, st->unit) ;
	st->top += 1 ;

	return 0 ;
}

int
pop (stack * st, void * elem)
{
	if (is_empty(st)) {
		printf("invalid") ;
		exit(0) ;
	}
	
	memcpy(elem, st->buffer + (st->top - 1) * st->unit, st->unit) ;
	st->top -= 1 ;
	return 0;
}

int 
is_empty (stack * st) 
{
	return (st->top == 0) ;
}

int 
is_full (stack * st) 
{
	return (st->top == st->capacity) ;
}

int
get_size (stack * st) 
{
	return st->top ;
}

int
get_element (stack * st, int index, void * elem)
{
	if (st->top <= index)
		return 1 ;

	memcpy(elem, st->buffer + index * st->unit, st->unit) ;
	return 0 ;
}
