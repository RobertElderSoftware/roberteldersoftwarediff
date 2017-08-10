#  Copyright 2017 Robert Elder Software Inc.
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.import random

import string
import sys
import os

"""
This file contains Python implementations for variations of algorithms described in 
'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.  A few optimizations
not mentioned in the paper are also included here.


* FUNCTIONS INCLUDED IN THIS FILE *

  -  diff(list1, list2)  - A function to determine the minimal difference between two sequences that
     is super easy to just copy and paste when you don't actually care about all the other stuff
     in this document, and you just need to get back to work because it's already 7pm and you're still
     at the office, and you just want to get this stupid thing to work, why is there no easy answer on
     Stack Overflow that I can just copy and paste?  Oh man, I really need to stop doing this and  
     start saying no to these crazy deadlines.  I have so many friends that I need to get back to and haven't
     spoken to in a while...  Maybe I'll just stay until most of my stock options vest, and then I'll
     quit.  This function has worst-case execution time of O(min(len(a),len(b)) * D), and requires
     2 * (2 * min(len(a),len(b))) space.

  -  apply_edit_script(edit_script, s1, s2) - An example function that shows how you could make use of
     the edit script returned by 'diff' or 'shortest_edit_script' by re-constructing s2 from s1 and the
     edit script.

  -  shortest_edit_script(old_sequence, new_sequence) - A well-formatted version of the diff function
     (mentioned above) that optimizes for code clarity and readability.  This version also calls out
     to the find_middle_snake function which it depends on.  This version of the algorithm is also
     presented in a way that attempts to match the description from the paper.

  -  longest_common_subsequence(list1, list2) - A function that returns a list that is the longest
     common sub-sequence of the two input sequences.

  -  find_middle_snake_less_memory(old_sequence, N, new_sequence, M) - A variant of the 'find middle
     snake' algorithm that has more restriced bounds so the calculation doesn't go off end end of the
     edit grid.  It has worst-case execution time of min(len(a),len(b)) * D, and requires
     2 * (2 * min(len(a),len(b))) space.

  -  find_middle_snake_myers_original(old_sequence, N, new_sequence, M) - A concrete implementation of
     the algorithm discussed in Myers' paper.  This algorithm has worst-case execution time of (M + N) * D
     and requires 2 * (M + N) space.

  -  myers_diff_length_minab_memory(old_sequence, new_sequence) - A version of the basic length measuring 
     algorithm that makes use of the restriced bounds, and also allocates less memory by treating the V
     array as a circular buffer.

  -  myers_diff_length_original_page_6(old_sequence, new_sequence) - A concrete implementation of the algorithm
     discussed on page 6 of Myers' paper.

  -  myers_diff_length_optimize_y_variant(old_sequence, new_sequence) - A variant of the basic length measuring 
     algorithm that optimized for the y variable instead of x.  It is helpful to study this version when
     attempting to understand the algorithm since the choice of optimizing x or y is rather arbitrary.

  -  Various other functions are included for testing.
"""

#  Returns a minimal list of differences between 2 lists e and f
#  requring O(min(len(e),len(f))) space and O(min(len(e),len(f)) * D)
#  worst-case execution time where D is the number of differences.
def diff(e, f, i=0, j=0):
    #  Documented at http://blog.robertelder.org/diff-algorithm/
    N,M,L,Z = len(e),len(f),len(e)+len(f),2*min(len(e),len(f))+2
    if N > 0 and M > 0:
        w,g,p = N-M,[0]*Z,[0]*Z
        for h in range(0, (L//2+(L%2!=0))+1):
            for r in range(0, 2):
                c,d,o,m = (g,p,1,1) if r==0 else (p,g,0,-1)
                for k in range(-(h-2*max(0,h-M)), h-2*max(0,h-N)+1, 2):
                    a = c[(k+1)%Z] if (k==-h or k!=h and c[(k-1)%Z]<c[(k+1)%Z]) else c[(k-1)%Z]+1
                    b = a-k
                    s,t = a,b
                    while a<N and b<M and e[(1-o)*N+m*a+(o-1)]==f[(1-o)*M+m*b+(o-1)]:
                        a,b = a+1,b+1
                    c[k%Z],z=a,-(k-w)
                    if L%2==o and z>=-(h-o) and z<=h-o and c[k%Z]+d[z%Z] >= N:
                        D,x,y,u,v = (2*h-1,s,t,a,b) if o==1 else (2*h,N-a,M-b,N-s,M-t)
                        if D > 1 or (x != u and y != v):
                            return diff(e[0:x],f[0:y],i,j)+diff(e[u:N],f[v:M],i+u,j+v)
                        elif M > N:
                            return diff([],f[N:M],i+N,j+N)
                        elif M < N:
                            return diff(e[M:N],[],i+M,j+M)
                        else:
                            return []
    elif N > 0: #  Modify the return statements below if you want a different edit script format
        return [{"operation": "delete", "position_old": i+n} for n in range(0,N)]
    else:
        return [{"operation": "insert", "position_old": i,"position_new":j+n} for n in range(0,M)]



def find_middle_snake_less_memory(old_sequence, N, new_sequence, M):
    """
    A variant of the 'find middle snake' function that uses O(min(len(a), len(b)))
    memory instead of O(len(a) + len(b)) memory.  This does not improve the
    worst-case memory requirement, but it takes the best case memory requirement 
    down to near zero.
    """
    MAX = N + M
    Delta = N - M
    
    V_SIZE=2*min(M,N) + 2
    Vf = [None] * V_SIZE
    Vb = [None] * V_SIZE
    Vf[1] = 0
    Vb[1] = 0
    for D in range(0, (MAX//2+(MAX%2!=0)) + 1):
        for k in range(-(D - 2*max(0, D-M)), D - 2*max(0, D-N) + 1, 2):
            if k == -D or k != D and Vf[(k - 1) % V_SIZE] < Vf[(k + 1) % V_SIZE]:
                x = Vf[(k + 1) % V_SIZE]
            else:
                x = Vf[(k - 1) % V_SIZE] + 1
            y = x - k
            x_i = x
            y_i = y
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            Vf[k % V_SIZE] = x
            inverse_k = (-(k - Delta))
            if (Delta % 2 == 1) and inverse_k >= -(D -1) and inverse_k <= (D -1):
                if Vf[k % V_SIZE] + Vb[inverse_k % V_SIZE] >= N:
                    return 2 * D -1, x_i, y_i, x, y
        for k in range(-(D - 2*max(0, D-M)), (D - 2*max(0, D-N)) + 1, 2):
            if k == -D or k != D and Vb[(k - 1) % V_SIZE] < Vb[(k + 1) % V_SIZE]:
                x = Vb[(k + 1) % V_SIZE]
            else:
                x = Vb[(k - 1) % V_SIZE] + 1
            y = x - k
            x_i = x
            y_i = y
            while x < N and y < M and old_sequence[N - x -1] == new_sequence[M - y - 1]:
                x = x + 1
                y = y + 1
            Vb[k % V_SIZE] = x
            inverse_k = (-(k - Delta))
            if (Delta % 2 == 0) and inverse_k >= -D and inverse_k <= D:
                if Vb[k % V_SIZE] + Vf[inverse_k % V_SIZE] >= N:
                    return 2 * D, N - x, M - y, N - x_i, M - y_i


def find_middle_snake_myers_original(old_sequence, N, new_sequence, M):
    """
    This function is a concrete implementation of the algorithm for 'finding the middle snake' presented
    similarly to the pseudocode on page 11 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.
    This algorithm is a centeral part of calculating either the smallest edit script for a pair of
    sequences, or finding the longest common sub-sequence (these are known to be dual problems).

    The worst-case (and expected case) space requirement of this function is O(N + M), where N is
    the length of the first sequence, and M is the length of the second sequence.
    The worst-case run time of this function is O(MN) and this occurs when both string have no common 
    sub-sequence.  Since the expected case is for the sequences to have some similarities, the expected
    run time is O((M + N)D) where D is the number of edits required to transform sequence A into sequence B.
    The space requirement remains the same in all cases, but less space could be used with a modified version
    of the algorithm that simply specified a user-defined MAX value less than M + N.  In this case, the
    algorithm would stop earlier and report a D value no greater than MAX, which would be interpreted as
    'there is no edit sequence less than length D that produces the new_sequence from old_sequence'.

    Note that (if I have understood the paper correctly), the k values used for the reverse direction
    of this implementation have opposite sign compared with those suggested in the paper.  I found this made 
    the algorithm easier to implement as it makes the forward and reverse directions more symmetric.

    @old_sequence  This represents a sequence of something that can be compared against 'new_sequence' 
    using the '==' operator.  It could be characters, or lines of text or something different.
    
    @N  The length of 'old_sequence'

    @new_sequence  The new sequence to compare 'old_sequence' against.

    @M  The length of 'new_sequence'

    There are 5 return values for this function:

    The first is an integer representing the number of edits (delete or insert) that are necessary to
    produce new_sequence from old_sequence.

    The next two parts of the return value are the point (x, y) representing the starting coordinate of the
    middle snake.

    The next two return values are the point (u, v) representing the end coordinate of the middle snake.

    It is possible that (x,y) == (u,v)
    """
    #  The sum of the length of the seqeunces.
    MAX = N + M
    #  The difference between the length of the sequences.
    Delta = N - M
    
    #  The array that holds the 'best possible x values' in search from top left to bottom right.
    Vf = [None] * (MAX + 2)
    #  The array that holds the 'best possible x values' in search from bottom right to top left.
    Vb = [None] * (MAX + 2)
    #  The initial point at (0, -1)
    Vf[1] = 0
    #  The initial point at (N, M+1)
    Vb[1] = 0
    #  We only need to iterate to ceil((max edit length)/2) because we're searching in both directions.
    for D in range(0, (MAX//2+(MAX%2!=0)) + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or k != D and Vf[k - 1] < Vf[k + 1]:
                #  Did not increase x, but we'll take the better (or only) x value from the k line above
                x = Vf[k + 1]
            else:
                #  We can increase x by building on the best path from the k line above
                x = Vf[k - 1] + 1
            #  From fundamental axiom of this algorithm: x - y = k
            y = x - k
            #  Remember the initial point before the snake so we can report it.
            x_i = x
            y_i = y
            #  While these sequences are identical, keep moving through the graph with no cost
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            #  This is the new best x value
            Vf[k] = x
            #  Only check for connections from the forward search when N - M is odd
            #  and when there is a reciprocal k line coming from the other direction.
            if (Delta % 2 == 1) and (-(k - Delta)) >= -(D -1) and (-(k - Delta)) <= (D -1):
                if Vf[k] + Vb[-(k - Delta)] >= N:
                    return 2 * D -1, x_i, y_i, x, y
        for k in range(-D, D + 1, 2):
            if k == -D or k != D and Vb[k - 1] < Vb[k + 1]:
                x = Vb[k + 1]
            else:
                x = Vb[k - 1] + 1
            y = x - k
            x_i = x
            y_i = y
            while x < N and y < M and old_sequence[N - x -1] == new_sequence[M - y - 1]:
                x = x + 1
                y = y + 1
            Vb[k] = x
            if (Delta % 2 == 0) and (-(k - Delta)) >= -D and (-(k - Delta)) <= D:
                if Vb[k] + Vf[(-(k - Delta))] >= N:
                    return 2 * D, N - x, M - y, N - x_i, M - y_i

def longest_common_subsequence_h(old_sequence, N, new_sequence, M):
    """
    This function is a concrete implementation of the algorithm for finding the longest common subsequence presented
    similarly to the pseudocode on page 12 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.

    @old_sequence  This represents a sequence of something that can be compared against 'new_sequence' 
    using the '==' operator.  It could be characters, or lines of text or something different.
    
    @N  The length of 'old_sequence'

    @new_sequence  The new sequence to compare 'old_sequence' against.

    @M  The length of 'new_sequence'

    The return value is a new sequence that is the longest common subsequence of old_sequence and new_sequence.
    """
    rtn = []
    if N > 0 and M > 0:
        D, x, y, u, v = find_middle_snake_less_memory(old_sequence, N, new_sequence, M)
        if D > 1:
            #  LCS(A[1..x],x,B[1..y],y)
            rtn.extend(longest_common_subsequence_h(old_sequence[0:x], x, new_sequence[0:y], y))
            #  Output A[x+1..u].
            rtn.extend(old_sequence[x:u])
            #  LCS(A[u+1..N],N-u,B[v+1..M],M-v)
            rtn.extend(longest_common_subsequence_h(old_sequence[u:N], N-u, new_sequence[(v):M], M-v))
        elif M > N:
            #  Output A[1..N].
            rtn.extend(old_sequence[0:N])
        else:
            #  Output B[1..M].
            rtn.extend(new_sequence[0:M])
    return rtn

def longest_common_subsequence(old_sequence, new_sequence):
    #  Just a helper function so you don't have to pass in the length of the sequences.
    return longest_common_subsequence_h(old_sequence, len(old_sequence), new_sequence, len(new_sequence));

def shortest_edit_script_h(old_sequence, N, new_sequence, M, current_x, current_y):
    """
    This function is a concrete implementation of the algorithm for finding the shortest edit script that was
    'left as an exercise' on page 12 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.

    @old_sequence  This represents a sequence of something that can be compared against 'new_sequence' 
    using the '==' operator.  It could be characters, or lines of text or something different.
    
    @N  The length of 'old_sequence'

    @new_sequence  The new sequence to compare 'old_sequence' against.

    @M  The length of 'new_sequence'

    The return value is a sequence of objects that contains the indicies in old_sequnce and new_sequnce that 
    you could use to produce new_sequence from old_sequence using the minimum number of edits.

    The format of this function as it is currently written is optimized for clarity, not efficiency.  It is
    expected that anyone wanting to use this function in a real application would modify the 2 lines noted
    below to produce whatever representation of the edit sequence you wanted.
    """
    rtn = []
    if N > 0 and M > 0:
        D, x, y, u, v = find_middle_snake_less_memory(old_sequence, N, new_sequence, M)
        #  If the graph represented by the current sequences can be further subdivided.
        if D > 1 or (x != u and y != v):
            #  Collection delete/inserts before the snake
            rtn.extend(shortest_edit_script_h(old_sequence[0:x], x, new_sequence[0:y], y, current_x, current_y))
            #  Collection delete/inserts after the snake
            rtn.extend(shortest_edit_script_h(old_sequence[u:N], N-u, new_sequence[v:M], M-v, current_x + u, current_y + v))
        elif M > N:
            #  M is longer than N, but we know there is a maximum of one edit to transform old_sequence into new_sequence
            #  The first N elements of both sequences in this case will represent the snake, and the last element
            #  will represent a single insertion.
            rtn.extend(shortest_edit_script_h(old_sequence[N:N], N-N, new_sequence[N:M], M-N, current_x + N, current_y + N))
        elif M < N:
            #  N is longer than (or equal to) M, but we know there is a maximum of one edit to transform old_sequence into new_sequence
            #  The first M elements of both sequences in this case will represent the snake, and the last element
            #  will represent a single deletion.  If M == N, then this reduces to a snake which does not contain any edits.
            rtn.extend(shortest_edit_script_h(old_sequence[M:N], N-M, new_sequence[M:M], M-M, current_x + M, current_y + M))
    elif N > 0:
        #  This area of the graph consist of only horizontal edges that represent deletions.
        for i in range(0, N):
            #  Modify this line if you want a more efficient representation:
            rtn.append({"operation": "delete", "position_old": current_x + i})
    else:
        #  This area of the graph consist of only vertical edges that represent insertions.
        for i in range(0, M):
            #  Modify this line if you want a more efficient representation:
            rtn.append({"operation": "insert", "position_old": current_x, "position_new": current_y + i})
    return rtn

def shortest_edit_script(old_sequence, new_sequence):
    #  Just a helper function so you don't have to pass in the length of the sequences.
    return shortest_edit_script_h(old_sequence, new_sequence, 0, 0);


def get_random_edit_script(old_sequence, new_sequence):
    """
    Used for testing.  The Myers algorithms should never produce an edit script
    that is longer than the random version.
    """
    es = []
    N = len(old_sequence)
    M = len(new_sequence)
    x = 0
    y = 0
    D = 0
    while not (x == N and y == M):
        while (x < N) and (y < M) and (old_sequence[x] == new_sequence[y]):
            x = x + 1
            y = y + 1
        if (x < N) and (y < M):
            if random.randint(0, 1):
                es.append({"operation": "delete", "position_old": x})
                x = x + 1
            else:
                es.append({"operation": "insert", "position_old": x, "position_new": y})
                y = y + 1
            D = D + 1
        elif x < N:
            es.append({"operation": "delete", "position_old": x})
            x = x + 1
            D = D + 1
        elif y < M:
            es.append({"operation": "insert", "position_old": x, "position_new": y})
            y = y + 1
            D = D + 1
    return es

def myers_diff_length_minab_memory(old_sequence, new_sequence):
    """
    A variant that uses min(len(a),len(b)) memory
    """
    N = len(old_sequence)
    M = len(new_sequence)
    MAX = N + M
    
    V_SIZE = 2*min(N,M) + 2
    V = [None] * V_SIZE
    V[1] = 0
    for D in range(0, MAX + 1):
        for k in range(-(D - 2*max(0, D-M)), D - 2*max(0, D-N) + 1, 2):
            if k == -D or k != D and V[(k - 1) % V_SIZE] < V[(k + 1) % V_SIZE]:
                x = V[(k + 1) % V_SIZE]
            else:
                x = V[(k - 1) % V_SIZE] + 1
            y = x - k
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            V[k % V_SIZE] = x
            if x == N and y == M:
                return D

def myers_diff_length_half_memory(old_sequence, new_sequence):
    """
    This function is a modified implementation of the algorithm for finding the length of the shortest edit
    script on page 6 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.

    This version uses 50% of the memory of the one described of page 6 of the paper, and has 50% of the
    worst-case execution time.

    The optimization comes from improving the calculation of the iteration bounds and replacing the line:

    for k in range(-D, D + 1, 2):

    from the original with

    for k in range(-(D - 2*max(0, D-M)), D - 2*max(0, D-N) + 1, 2):

    This optimization works by maintaining tighter bounds on k by measuring how far off the edit grid
    the current value of D would take us if we to look at points on the line k = D.  The overshoot
    distance is equal to D-N on the right edge of the edit grid, and D-M on the bottom edge of the edit
    grid.
    """
    N = len(old_sequence)
    M = len(new_sequence)
    MAX = N + M
    
    V = [None] * (MAX + 2)
    V[1] = 0
    for D in range(0, MAX + 1):
        for k in range(-(D - 2*max(0, D-M)), D - 2*max(0, D-N) + 1, 2):
            if k == -D or k != D and V[k - 1] < V[k + 1]:
                x = V[k + 1]
            else:
                x = V[k - 1] + 1
            y = x - k
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            V[k] = x
            if x == N and y == M:
                return D


def myers_diff_length_original_page_6(old_sequence, new_sequence):
    """
    This function is a concrete implementation of the algorithm for finding the length of the shortest edit
    script on page 6 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.

    @old_sequence  This represents a sequence of something that can be compared against 'new_sequence' 
    using the '==' operator.  It could be characters, or lines of text or something different.
    
    @new_sequence  The new sequence to compare 'old_sequence' against.

    The return value is an integer describing the minimum number of edits required to produce new_sequence
    from old_sequence.  If no edits are required the return value is 0.  Since this function only returns
    the length of the shortest edit sequence, you must use another function (included here) to recover
    the edit sequence.  You can also modify this version to do it, but this requires O((M+N)^2) memory.

    The format of this function as it is currently written is optimized for clarity and to match
    the version found in the referenced paper.  There are a few optimizations that can be done to 
    decrease the memory requirements, and those have been done in another function here.
    
    """
    N = len(old_sequence)
    M = len(new_sequence)
    MAX = N + M

    #  The +2 ensures we don't get an access violation when N + M = 0, since we need to
    #  consider at least 2 points for a comparison of empty sequences.
    #  The 2*MAX can be reduced to just MAX using more intelligent bounds calculation
    #  instead of just iterating from -D to D.
    V = [None] * (2 * MAX + 2)
    V[1] = 0
    for D in range(0, MAX + 1):
        #  The range -D to D expands as we move diagonally accross the rectangular edit grid.
        for k in range(-D, D + 1, 2):
            #  If k is against the left wall, or (not aginst the top wall and there is a
            #  k line that has reached a higher x value above the current k line)
            if k == -D or k != D and V[k - 1] < V[k + 1]:
                #  Extend the path from the k line above to add an insertion to the path.
                #  V[] measures the best x values, so we don't need to increment x here.
                x = V[k + 1]
            else:
                #  Otherwise, V[k - 1] >= V[k + 1], or K == D which means that we
                #  use the k line from below to extend the best path, and since this
                #  path is a horizontal one (a deletion), we increment x.
                x = V[k - 1] + 1
            #  From the axiom of the algorithm:  x - y = k
            y = x - k
            #  Move through the diagonal that has 0 edit cost (strings are same here)
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            #  Store our new best x value
            V[k] = x
            #  Have we completely moved through the grid?
            if x >= N and y >= M:
                return D


def myers_diff_length_optimize_y_variant(old_sequence, new_sequence):
    """
    This function is a variant of the algorithm for finding the length of the shortest edit
    script on page 6 of 'An O(ND) Difference Algorithm and Its Variations' by EUGENE W. MYERS.

    This version optimizes the variable y instead of x.
    """
    N = len(old_sequence)
    M = len(new_sequence)
    MAX = N + M

    V = [None] * (2 * MAX + 2)
    V[-1] = 0
    for D in range(0, MAX + 1):
        for k in range(-D, D + 1, 2):
            if k == D or k != -D and V[k - 1] > V[k + 1]:
                y = V[k - 1]
            else:
                y = V[k + 1] + 1
            x = y + k
            while x < N and y < M and old_sequence[x] == new_sequence[y]:
                x = x + 1
                y = y + 1
            V[k] = y
            if x >= N and y >= M:
                return D


def generate_alphabet():
    """
    This function is used for testing.
    """
    alphabet_size = random.randint(1, len(string.ascii_letters))
    return [random.choice(string.ascii_letters) for i in range(0, alphabet_size)]

class EditGraph(object):
    """
    When testing the myers diff algorithm and its variants, it is meaningful to test by
    first constructing an edit graph, and solving for a sequence that would match
    that edit graph as closely as possible.

    Randomly generating statistically independent sequences won't cover as many cases of
    program execution as 'real' sequences that have some intrinsic relationship between
    them.

    In this class, an 'edit graph' is constructed with random dimensions and filled with
    random diagonals.  The 'solve sequences' method then attempts to build two sequences
    that would have produced this edit graph as closely as possible.

    Note that it is not always possible to produce a pair of sequences that would exactly
    produce these randomly generated edit graphs because you can draw an 'impossible'
    edit graph where the implied relationship of diagonals would deduce that some squares
    that are not diagonals must in fact be diagonals.  The code below, simply solves
    for the 'equal to' constraints and ignores the 'not equal to' constraint of empty
    squares.  Therefore, the sequences that get solved for will likely not have exactly
    the same edit graph that was created, but at least it will be close and produce
    a pair of sequences with an intrinsic relationship between them.
    """
    def __init__(self, x, y, diagonal_probability):
        self.x = x
        self.y = y
        self.diagonal_probability = diagonal_probability
        self.graph = []
        self.make_empty_edit_graph(x, y)
        self.add_random_diagonals_to_edit_graph()

    def make_empty_edit_graph(self, x, y):
        for i in range(0,y):
            r = []
            for j in range(0,x):
                r.append(False)
            self.graph.append(r)

    def print_edit_graph(self):
        for i in range(0, self.y):
            r = self.graph[i]
    
            if i == 0:
                sys.stdout.write("+")
                for j in range(0, len(r)):
                    sys.stdout.write("-+")
                sys.stdout.write("\n")
            sys.stdout.write("|")
            for j in range(0, len(r)):
                if r[j]["is_diagonal"]:
                    sys.stdout.write("\\|")
                else:
                    sys.stdout.write(" |")
            sys.stdout.write("\n")
            sys.stdout.write("+")
            for j in range(0, len(r)):
                sys.stdout.write("-+")
            sys.stdout.write("\n")

    def solve_edit_graph(self):
        #  Attempt to assign symbols to the input strings that produced this edit graph.
        s1 = []
        for i in range(0, self.x):
            s1.append({})
        s2 = []
        for i in range(0, self.y):
            s2.append({})
        current_symbol = 0
        for j in range(0, self.y):
            for i in range(0, self.x):
                if self.graph[j][i]["is_diagonal"]:
                    used_symbol = False
                    points = [{"x": i, "y": j}]
                    while len(points):
                        new_points = []
                        for g in range(0, len(points)):
                            if not (("has_symbol" in s1[points[g]["x"]]) and ("has_symbol" in s2[points[g]["y"]])):
                                if self.graph[points[g]["y"]][points[g]["x"]]["is_diagonal"]:
                                    if self.assign_symbol(points[g]["x"], points[g]["y"], s1, s2, current_symbol):
                                        used_symbol = True
                                    if self.assign_symbol(points[g]["x"], points[g]["y"], s1, s2, current_symbol):
                                        used_symbol = True
                                    for k in range(0, self.y):
                                        if self.graph[k][points[g]["x"]]["is_diagonal"] and k != points[g]["y"]:
                                            new_points.append({"x": points[g]["x"], "y": k})
                                    for k in range(0, self.x):
                                        if self.graph[points[g]["y"]][k]["is_diagonal"] and k != points[g]["x"]:
                                            new_points.append({"x": k, "y": points[g]["y"]})
                        points = new_points
                        if(len(points) > 0):
                            used_symbol = True
                    if used_symbol:
                        current_symbol = current_symbol + 1
        return self.solve_sequences(s1, s2, current_symbol)

    def add_random_diagonals_to_edit_graph(self):
        for i in range(0, self.y):
            for j in range(0, self.x):
                if random.randint(0,self.diagonal_probability) == 0:
                    self.graph[i][j] = {"is_diagonal": True}
                else:
                    self.graph[i][j] = {"is_diagonal": False}

    def assign_symbol(self, i, j, s1, s2, current_symbol):
        made_assignment = False
        if "has_symbol" in s1[i]:
            if s1[i]["has_symbol"] != current_symbol:
                raise
        else:
            s1[i]["has_symbol"] = current_symbol
            made_assignment = True
        
        if "has_symbol" in s2[j]:
            if s2[j]["has_symbol"] != current_symbol:
                raise
        else:
            s2[j]["has_symbol"] = current_symbol
            made_assignment = True
        
        return made_assignment

    def solve_sequences(self, s1, s2, current_symbol):
        r1 = []
        r2 = []
        for i in range(0, len(s1)):
            if "has_symbol" in s1[i]:
                r1.append(s1[i]["has_symbol"])
            else:
                r1.append(current_symbol)
                current_symbol = current_symbol + 1
        
        for i in range(0, len(s2)):
            if "has_symbol" in s2[i]:
                r2.append(s2[i]["has_symbol"])
            else:
                r2.append(current_symbol)
                current_symbol = current_symbol + 1
        
        return r1, r2

def make_random_sequences(size):
    choice = random.randint(0,2)
    if choice == 0:
        #  Construct an edit graph, and then build a sequences that matches it as closely as possible
        eg = EditGraph(random.randint(0, size), random.randint(0, size), random.randint(1, size))
        s1, s2 = eg.solve_edit_graph()
        return s1, s2
    elif choice == 1:
        string_a_size = random.randint(0, size)
        string_b_size = random.randint(0, size)
        s1 = list(''.join(random.choice(generate_alphabet()) for i in range(string_a_size)))
        s2 = list(''.join(random.choice(generate_alphabet()) for i in range(string_b_size)))
        return s1, s2
    else:
        special_cases = [
            [
                #  Both empty
                [], []
            ],
            [
                #  Not empty, empty
                [1], []
            ],
            [
                #  Empty, Not empty
                [], [1]
            ],
            [
                #  Not empty, empty
                [1,2], []
            ],
            [
                #  Empty, Not empty
                [], [1,2]
            ],
            [
                #  Both identical
                [1,2,3,4], [1,2,3,4]
            ],
            [
                #  Both different
                [1,2,3,4], [5,6,7,8]
            ],
            [
                #  Half size of the second
                [1,2,3,4], [5,6,7,8,'a','b','c','d']
            ],
            [
                #  Half size of the first
                [5,6,7,8,'a','b','c','d'], [1,2,3,4]
            ],
            [
                #  2n + 1 size of the second
                [5,6,7,8,'a','b','c','d','e'], [1,2,3,4]
            ],
            [
                #  2n + 1 size of the first
                [1,2,3,4], [5,6,7,8,'a','b','c','d','e']
            ],
            [
                #  Odd size, odd size
                [5,6,7], [1,2,3]
            ],
            [
                #  Odd size, even size
                [5,6,7], [1,2,3,4]
            ],
            [
                #  Even size, even size
                [5,6,7,8], [1,2,3,4]
            ],
            [
                #  Even size, odd size
                [5,6,7,8], [1,2,3]
            ]
        ]
        case_number = random.randint(0, len(special_cases) -1)
        
        return special_cases[case_number][0], special_cases[case_number][1]

def apply_edit_script(edit_script, s1, s2):
    new_sequence = []
    i = 0
    for e in edit_script:
        while e["position_old"] > i:
            if i < len(s1):
                new_sequence.append(s1[i])
            i = i + 1
        if e["position_old"] == i:
            if e["operation"] == "delete":
                i = i + 1
            elif e["operation"] == "insert":
                new_sequence.append(s2[e["position_new"]])
            elif e["operation"] == "change":
                new_sequence.append(s2[e["position_new"]])
                i = i + 1
        else:
            #  Should not happen
            raise 

    while i < len(s1):
        new_sequence.append(s1[i])
        i = i + 1
    return new_sequence

def get_parts_for_change_region(edit_script, i, ins, dels):
    parts = []
    #  This is the size of the 'changed' region.
    square_size = min(len(ins), len(dels))
    #  These are the inserts and deletes that have been paired up
    for n in range(0, square_size):
        parts.append({"operation": "change", "position_old": edit_script[dels[n]]["position_old"] ,"position_new": edit_script[ins[n]]["position_new"]})
    #  These are the leftover inserts, that must be pushed 'square_size' units to the right.
    for n in range(square_size, len(ins)):
        m = edit_script[ins[n]]
        #  Adjust the insertion positions so the offsets make sense in the simplified path.
        shift_right = square_size - (m["position_old"] - edit_script[i]["position_old"])
        p = {"operation": "insert", "position_old": m["position_old"] + shift_right, "position_new": m["position_new"]}
        parts.append(p)

    #  These are the leftover deletes.
    for n in range(square_size, len(dels)):
        m = edit_script[dels[n]]
        parts.append(m)

    return parts


def simplify_edit_script(edit_script):
    #  If we find a contiguous path composed of inserts and deletes, make them into 'changes' so they
    #  can produce more visually pleasing diffs.
    new_edit_script = []
    m = len(edit_script)
    i = 0
    while i < m:
        others = []
        ins = []
        dels = []
        last_indx = edit_script[i]["position_old"]
        #  Follow the path of inserts and deletes
        while i + len(ins) + len(dels) < m:
            indx = i + len(ins) + len(dels)
            edit = edit_script[indx]
            if edit["operation"] == "insert" and edit["position_old"] == last_indx:
                last_indx = edit["position_old"]
                ins.append(indx)
            elif edit["operation"] == "delete" and edit["position_old"] == last_indx:
                last_indx = edit["position_old"] + 1
                dels.append(indx)
            else:
                if edit["operation"] == "insert" or edit["operation"] == "delete":
                    pass #  Non-contiguous insert or delete.
                else:  #  The current edit is something other than delete or insert, just add it...
                    others.append(indx)
                break
        if len(ins) > 0 and len(dels) > 0:
            #  Do simplify
            new_edit_script.extend(get_parts_for_change_region(edit_script, i, ins, dels))
        else:
            #  Add the lone sequence of deletes or inserts
            for r in range(0, len(dels)):
                new_edit_script.append(edit_script[dels[r]])
            for r in range(0, len(ins)):
                new_edit_script.append(edit_script[ins[r]])
        for r in range(0, len(others)):
            new_edit_script.append(edit_script[others[r]])
        i += len(ins) + len(dels) + len(others)
    return new_edit_script

def compare_sequences(s1, s2):
    if len(s1) == len(s2):
        for i in range(0, len(s1)):
            if s1[i] != s2[i]:
                return False
        return True
    else:
        return False

def print_edit_sequence(es, s1, s2):
    for e in es:
        if e["operation"] == "delete":
            print("Delete " + str(s1[e["position_old"]]) + " from s1 at position " + str(e["position_old"]) + " in s1.")
        elif e["operation"] == "insert":
            print("Insert " + str(s2[e["position_new"]]) + " from s2 before position " + str(e["position_old"]) + " into s1.")
        elif e["operation"] == "change":
            print("Change " + str(s1[e["position_old"]]) + " from s1 at position " + str(e["position_old"]) + " to be " + str(s2[e["position_new"]]) + " from s2.")
        else:
            raise

def do_external_diff_test(s1, s2):
    echo1 = "echo -en '"+ ("\\\\n".join([str(i) for i in s1])) + "'"
    echo2 = "echo -en '"+ ("\\\\n".join([str(i) for i in s2])) + "'"
    output1 = os.popen("/bin/bash -c \"../diffutils/original_diff_executable <(" + echo1 + ") <(" + echo2 + ") --minimal\"", 'r').read()
    output2 = os.popen("/bin/bash -c \"../diffutils-3.6/src/diff <(" + echo1 + ") <(" + echo2 + ") --minimal\"", 'r').read()
    output3 = os.popen("/bin/bash -c \"../original_diff_executable <(" + echo1 + ") <(" + echo2 + ")\"", 'r').read()
    output4 = os.popen("/bin/bash -c \"../diffutils-3.6/src/diff <(" + echo1 + ") <(" + echo2 + ")\"", 'r').read()
    #print("Echos were " + echo1 + " " + echo2)
    if output1 == output2 and output3 == output4:
        print("Diff matches.")
    else:
        print("FAIL! Diff does not match s1=")
        assert(0)

def do_test():
    s1, s2 = make_random_sequences(random.randint(1,300))

    print("Begin test with sequences a=" + str(s1) + " and b=" + str(s2) + "")

    #  Edit script
    minimal_edit_script = diff(s1, s2)
    random_edit_script = get_random_edit_script(s1, s2)

    reconstructed_minimal_sequence_basic = apply_edit_script(minimal_edit_script, s1, s2)
    reconstructed_minimal_sequence_simple = apply_edit_script(simplify_edit_script(minimal_edit_script), s1, s2)

    #  Random edit scripts encounter cases that the more optimal myers script don't
    reconstructed_random_sequence_basic = apply_edit_script(random_edit_script, s1, s2)
    reconstructed_random_sequence_simple = apply_edit_script(simplify_edit_script(random_edit_script), s1, s2)

    #  Pick out only the deletions
    only_deletes = [item for item in minimal_edit_script if not item["operation"] == "insert"]
    #  If we only apply the deletions to the original sequence, this should
    #  give us the longest common sub-sequence.
    reconstructed_lcs_sequence = apply_edit_script(only_deletes, s1, [])
 
    #  Longest common subsequence
    lcs = longest_common_subsequence(s1, s2)

    #  Edit script length calculations
    optimal_distance = myers_diff_length_original_page_6(s1, s2)
    half_memory_distance = myers_diff_length_half_memory(s1, s2)
    minab_memory_distance = myers_diff_length_minab_memory(s1, s2)
    optimize_y_distance = myers_diff_length_optimize_y_variant(s1, s2)
    random_distance = len(random_edit_script)
    edit_script_length = len(minimal_edit_script)
    #  D = (M + N) + L
    computed_distance = (len(s1) + len(s2)) - (2 * (len(lcs)))

    #  Snake finding algorithms
    D1, x1, y1, u1, v1 = find_middle_snake_less_memory(s1, len(s1), s2, len(s2))
    D2, x2, y2, u2, v2 = find_middle_snake_myers_original(s1, len(s1), s2, len(s2))

    #do_external_diff_test(s1, s2)

    if not (
        D1 == D2 and
        x1 == x2 and
        y1 == y2 and
        u1 == u2 and
        v1 == v2 and
        reconstructed_lcs_sequence == lcs and
        optimal_distance == edit_script_length and
        optimal_distance == computed_distance and
        optimal_distance == half_memory_distance and
        optimal_distance == minab_memory_distance and
        optimal_distance == optimize_y_distance and
        random_distance >= optimal_distance and
        compare_sequences(reconstructed_minimal_sequence_basic, s2) and
        compare_sequences(reconstructed_minimal_sequence_simple, s2) and
        compare_sequences(reconstructed_random_sequence_basic, s2) and
        compare_sequences(reconstructed_random_sequence_simple, s2)
    ):
        print("FAILURE!!!!")
        print("Sequences are a=" + str(s1) + " and b=" + str(s2) + "")
        print("optimal D: " + str(optimal_distance))
        print("computed D: " + str(computed_distance))
        print("half memory D: " + str(half_memory_distance))
        print("min A,B memory D: " + str(minab_memory_distance))
        print("Optimize y D: " + str(optimize_y_distance))
        print("random D: " + str(random_distance))
        print("reconstructed_minimal_sequence_basic: " + str(reconstructed_minimal_sequence_basic))
        print("reconstructed_minimal_sequence_simple: " + str(reconstructed_minimal_sequence_simple))
        print("reconstructed_random_sequence_basic: " + str(reconstructed_random_sequence_basic))
        print("reconstructed_random_sequence_simple: " + str(reconstructed_random_sequence_simple))
        print("edit_script_length: " + str(edit_script_length))
        print("Less memory Snake: D=" + str(D1) + " x1=" + str(x1) + " y1=" + str(y1) + " u1=" + str(u1) + " v1=" + str(v1))
        print("Myers original Snake: D=" + str(D2) + " x2=" + str(x2) + " y2=" + str(y2) + " u2=" + str(u2) + " v2=" + str(v2))
        sys.stdout.flush()
        assert(0)
    else:
        print("Pass")

#random.seed(123)  #  For deterministic test result comparisons.

i = 0
while True:
    do_test()
    i=i+1
