#define _POSIX_SOURCE
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdlib.h>
#include <stdlib.h>
#include <fcntl.h>
#include <signal.h>
int main(int argc, char *argv[])
{
	if(argc == 1){
        return EINVAL;    
	} 
    int test; 
    int * filedes = (int *)malloc(sizeof(int)*2*(argc-2)); 
    // (# of args - 1) == # of commands execd
    // # of commands execd - 1 = # of pipes 
    // malloc -> ( # of args - 2 ) * 2 * 4 bytes 
    if(!filedes)
        return errno; 
    pid_t * wait_pid = (pid_t *)malloc(sizeof(pid_t)*(argc-1)); 
    if(!wait_pid)
        return errno; 
    for(int i = 0; i < (argc-1); i++){
        wait_pid[i]=0; 
    }
    for(int i = 0; i < argc - 2; i++){
        test = pipe(&filedes[2*i]); 
        if(test == -1)
            return errno; 

    }
    int spawned_processes = 0; 
    for(int i = 1; i < (argc); i++){
        pid_t pid = fork(); 
        if(pid == -1){
            return errno; 
        }
        if(pid == 0) { // child process
            if(i == 1){
                if(argc!=2){
                    test = dup2(filedes[1], 1); 
                    if(test == -1)
                        return errno;           
                 } 
            }else if(i+1!=argc){

                test = dup2(filedes[2*(i-2)], 0); 
                if(test == -1)
                    return errno;  
                test = dup2(filedes[2*(i-2)+3], 1); 
                if(test == -1)
                    return errno; 
                
            } else {
                test = dup2(filedes[2*(i-2)], 0); 
                if(test == -1)
                    return errno; 
                
            }
            // close all file descriptors 
            // STDIN & STDOUT already set, don't need any others open 
            for(int j = 0; j < 2*(argc-2); j++){
                    if(fcntl(filedes[j], F_GETFD)!=-1){
                        test = close(filedes[j]); 
                        if(test == -1)
                            return errno; 
                    } 
                } 
            int exec_return = execlp(argv[i], argv[i], NULL); 
            if(exec_return == -1) {
                return errno; 
            } 

        } else { 
            // leave all fds open so child processes can choose 
            // which ones they want 
            spawned_processes++; 
            wait_pid[i-1] = pid; 
        }
    }
    for(int j = 0; j < 2*(argc-2); j++){ // close file descriptors 
        if(fcntl(filedes[j], F_GETFD)!=-1){
            test = close(filedes[j]); 
            if(test == -1)
                return errno; 
        }
    } 
    // wait on all the processes
    for(int i = 0; i < spawned_processes;){
        int wstatus; 
        pid_t pid = wait(&wstatus); 
        if(pid == -1){
            return errno; 
        } else if(pid > 0){
            if(WIFEXITED(wstatus)){
                if(WEXITSTATUS(wstatus)!=0){
                    for(int j = 0; j < (argc-1); j++){
                        if(wait_pid[j]!=0 && wait_pid[j]!=pid){
                            kill(wait_pid[j], 15); 
                            wait_pid[j]=0; 
                        }
                    }
                    free(filedes); 
                    free(wait_pid);
                    return WEXITSTATUS(wstatus); 
                }
                for(int j = 0; j < (argc-1); j++){
                    if(wait_pid[j] == pid){
                        wait_pid[j]=0; 
                        break;
                    }
                } 
                spawned_processes--;
            } 
        }
    }
    free(filedes); 
    free(wait_pid);
	return 0;
}
