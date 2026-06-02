#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <time.h>

/*
 * Code to analyze the RSE problem in low dimensions. The code is based on brute-force technique, 
 * but it is highly optimized in actual implementation.
 * 
 * The C function is invoked with one argument, the dimension d, and also enables an optional setting 
 * to force a single vertex (the ``wild" state 0) to always be a source. Subject to that setting, the 
 * code exhausts over all possible orientations of a $d$-dimensional boolean lattice using reflected 
 * binary Gray codes (so that the exhaustive search is performed with each orientation obtained from 
 * the previous orientation by reversing a single edge.) For each orientation, it first checks to ensure 
 * the orientation is acyclic using a depth-first search. If so, the code computes the number of 
 * instances of RSE as well as the number of sinks, each from scratch again using brute force. The 
 * output of the algorithm is a two-dimensional table A of counts where entry A[r][s] gives the number 
 * of acyclic orientations having r instances of RSE and s sinks.
 * 
 * Compile with
 *      gcc orientations.c -o orientations
 * and then run with 
 *      ./orientations 3
 * or whatever dimension is desired. (Should work up to dimension 4.)
 * 
 * Also, see constants below for additional options.
 * 
 */

#define VERBOSE 1
#define WILDISSOURCE 1    // set to 1 to designate a certain vertex (the "wild" one) as always a source
#define REPORTPROGRESS 1
#define RETURNCYCLE 0
#define REPORTCYCLE 0

#define BYTE_TO_BINARY_PATTERN "%c%c%c%c%c%c%c%c"
#define BYTE_TO_BINARY(byte)  \
  (byte & 0x80 ? '1' : '0'), \
  (byte & 0x40 ? '1' : '0'), \
  (byte & 0x20 ? '1' : '0'), \
  (byte & 0x10 ? '1' : '0'), \
  (byte & 0x08 ? '1' : '0'), \
  (byte & 0x04 ? '1' : '0'), \
  (byte & 0x02 ? '1' : '0'), \
  (byte & 0x01 ? '1' : '0') 


struct vertexPos
{
    int32_t vert;
    int32_t pos;
};

int ipow(int base, int exp)
{
    int result = 1;
    for (;;)
    {
        if (exp & 1)
            result *= base;
        exp >>= 1;
        if (!exp)
            break;
        base *= base;
    }

    return result;
}

char* binary_lastn(int32_t value, char* result, int32_t num_chars) {
  char* ptr = result;
  while (num_chars--) {
    *ptr++ = ((value >> num_chars) & 1) ? '1' : '0';
  }  
  *ptr = '\0';
  return result;
}

void print_binary(int32_t len, int32_t val) {
    char buffer[len+1];
    binary_lastn(val,buffer,len);
    printf("%s",buffer);
}


int32_t** init_orientation(int32_t num_verts, int32_t dim) {
  int32_t** ori = calloc(num_verts, sizeof(int32_t*));
  ori[0] = calloc(num_verts * dim, sizeof(int32_t));
  for (int32_t v = 1; v < num_verts; v++) {
    ori[v] = (int32_t*) (ori[v-1] + dim);
  }
  return ori;
}

// Indices the edges of the graph, by mapping each index from 0 to num_edges - 1 to a vertex v with
// a 1 in position p (0-indexed left-to-right) along with the position p; this then represents the
// edge from [v with position p flipped to 0] to [v].
// Note that the outgoing edges from the all-0 vertex are encountered first, so they correspond to indices
// 0, 1, ..., p-1.
struct vertexPos * init_edge_map(int32_t num_edges, int32_t num_verts, int32_t dim, int32_t** ori) {
  struct vertexPos *edge_map = calloc(num_edges, sizeof(struct vertexPos));
  int32_t edge_index = 0;
  for (int32_t v = 0; v < num_verts; v++) {
    for (int32_t p = dim-1; p >= 0; p--) {
      if (!(v & (1 << p))) {  // if v has 0 in pth location
	edge_map[edge_index].vert = (v ^ (1 << p)); // set edge_map[edge_index].vert to v's neighbor in this position
        edge_map[edge_index].pos  = p;               // set edge_map[edge_index].pos to the position
#if (VERBOSE >= 1)
	printf("Edge %d from vertex %x to vertex %x; pos = %d\n",edge_index,v, v ^ (1 << p),p);
#endif
        edge_index++;
      }
    }
  }
  return edge_map;
}

void set_orientation_to_allforward(struct vertexPos * edge_map, int32_t num_verts, int32_t dim, int32_t** ori) {
  for (int32_t v = 0; v < num_verts; v++) {
    for (int32_t p = 0; p < dim; p++) {
      if (v & (1 << p)) {  // if v has 1 in pth location
	ori[v][p] = 0;
	ori[v ^ (1 << p)][p] = 1;
      }
    }
  }
}


void print_orientation(int32_t num_verts, int32_t dim, int32_t** ori) {
  for (int32_t v = 0; v < num_verts; v++) {
    print_binary(dim, v);
    for (int32_t p = 0; p < dim; p++) {
      printf("   %s ",ori[v][p] ? "->" : "  ");
      print_binary(dim, v ^ (1 << p));
    }
    printf("\n");
  }
}


void print_orientation_adjlist(int32_t num_verts, int32_t dim, int32_t** ori) {
  for (int32_t v = 0; v < num_verts; v++) {
    print_binary(dim, v);
    printf(" : ");
    for (int32_t p = 0; p < dim; p++) {
      if (ori[v][p]) {
	print_binary(dim, v ^ (1 << p));
	printf(" ");
      }
    }
    printf("\n");
  }
}


int32_t dfs(int32_t curr_vert, 
	    int32_t* on_stack, 
	    int32_t* visited, 
	    int32_t* cycle, 
	    int32_t dim, 
	    int32_t** ori) {
  on_stack[curr_vert] = 1;
  int32_t found_cycle = 0;
  for (int32_t pos = 0; pos < dim; pos++) { // For each possible edge
    if (!found_cycle && ori[curr_vert][pos]) { // Continue if haven't found cycle, and this is a forward edge
      if (visited[curr_vert ^ (1 << pos)] < 0) { // If neighbor not visited, then proceed with DFS
	visited[curr_vert ^ (1 << pos)] = curr_vert; // Visit neighbor; track its previous (which is curr)
	found_cycle = dfs(curr_vert ^ (1 << pos), on_stack, visited, cycle, dim, ori); // DFS step
      } else {
	if (on_stack[curr_vert ^ (1 << pos)]) {  // If neighbor is on stack, then there's a cycle.
#if RETURNCYCLE
	  // Find it (in reverse order).
	  int32_t walk_back_vert = curr_vert;
	  int32_t walk_pos = 0;
	  while (walk_back_vert != (curr_vert ^ (1 << pos))) {
	    cycle[walk_pos++] = walk_back_vert;
	    walk_back_vert = visited[walk_back_vert];
	  }
	  cycle[walk_pos++] = curr_vert ^ (1 << pos);
	  found_cycle = walk_pos;
#else
	  found_cycle = 1;
#endif
	}
      }
    }
  }
  on_stack[curr_vert] = 0;
  return found_cycle;
}

int32_t has_cycle(int32_t* cycle, int32_t* on_stack, int32_t* visited, int32_t num_verts, int32_t dim, int32_t** ori) {
  for (int32_t i = 0; i < num_verts; i++) {
    visited[i] = -1;
    on_stack[i] = 0;
  }

  int32_t found_cycle = 0;
  for (int32_t start_vert = 0; start_vert < num_verts; start_vert++) {
    if (visited[start_vert] < 0) {
      visited[start_vert] = num_verts; // no prev vertex in DFS, so placeholder for "start vertex"
      if ((found_cycle = dfs(start_vert, on_stack, visited, cycle, dim, ori))) {
	return found_cycle;
      }
    }
  }
  return found_cycle;
}



void free_orientation(int32_t** ori) {
  free(ori[0]);
  free(ori);
}

void free_edge_map(struct vertexPos *edge_map) {
  free(edge_map);
}

int cycle_contains_edge(int32_t* cycle, int32_t cyc_len, int32_t edge_ind) {
  for (int32_t i = 0; i < cyc_len; i++) {
    if (cycle[i] == edge_ind) {
      return 1;
    }
  }
  return 0;
}

int32_t count_rse(int32_t num_verts, int32_t dim, int32_t** ori) {
  int32_t rse_count = 0;
  for (int32_t v = 0; v < num_verts; v++) {
    for (int32_t pos1 = 0; pos1 < dim - 1; pos1++) {
      for (int32_t pos2 = pos1 + 1; pos2 < dim; pos2++) {
	if ((v & (1 << pos1)) && (v & (1 << pos2))) { // To avoid quadruple-counting, proceed only
	                                              // if both pos1 and pos2 positions in v are 1
	  int32_t vo = v ^ (1 << pos1) ^ (1 << pos2); // Opposite vertex (with pos1 & pos2 0's)
	  rse_count +=
	     (ori[v][pos1] && ori[v][pos2] && ori[vo][pos1] && ori[vo][pos2]) ||
	    !(ori[v][pos1] || ori[v][pos2] || ori[vo][pos1] || ori[vo][pos2]);
	  // Add one if v and vo have only outgoing edges in pos1 & pos2 directions,
	  // or if none of these edges are outgoing.
	}
      }
    }
  }
  return rse_count;
}

int32_t count_sinks(int32_t num_verts, int32_t dim, int32_t** ori) {
  int32_t sink_count = 0;
  for (int32_t v = 0; v < num_verts; v++) {
    int32_t has_outgoing_edge = 0;
    for (int32_t pos = 0; pos < dim; pos++) {
      has_outgoing_edge |= ori[v][pos];
    }
    sink_count += !has_outgoing_edge;
  }
  return sink_count;
}



int main(int argc, char *argv[]) {
  if (argc < 2) {
    printf("Please provide the dimension.\n");
    return -1;
  }

  int32_t dim = atoi(argv[1]);


  int32_t num_verts = 1 << dim;  // == 2^dim
  int32_t num_edges = dim * (1 << (dim - 1)); // choose a position
  // (dim possible), then set the other (dim-1) entries to any of the
  // 2^(dim-1) == num_verts / 2 possibilities


  // Vertices are represented by the integers 0 through num_verts - 1
  // The neighbors of a vertex x are
  //   x ^ 1,   x ^ (1 << 1),  x ^ (1 << 2),  ...,  x ^ (1 << dim - 1).

  // An orientation is represented by a binary 2D array, ori, of size
  //         num_verts  x  dim
  // where ori[v][p] = 1 if there's an directed edge from v to v ^ (1 << p)
  // and 0 if the edge is directed the other way.
  // For consistency, we enforce that
  //         ori[v][p] + ori[v ^ (1 << p)][p] == 1,
  // (i.e., one is 1 and the other 0)
  // for all 0 <= v < num_verts  and  0 <= p < dim.

  int32_t rses_values_poss = ((1 << (dim - 2))*dim*(dim-1)/2) + 1;
  int32_t sinks_values_poss = (1 << (dim - 1)) + 1;

#if (VERBOSE >=1)
  printf("dim: %d,  num_verts: %d,  num_edges: %d\n",dim, num_verts, num_edges);
#endif
  
  int64_t **ori_count_by_sinks_rses = (int64_t**) calloc(sinks_values_poss, sizeof(int64_t*));
  
  ori_count_by_sinks_rses[0] = (int64_t*) calloc(sinks_values_poss * rses_values_poss, sizeof(int64_t));
  for (int32_t i = 0; i < sinks_values_poss; i++) {
    ori_count_by_sinks_rses[i] =  ori_count_by_sinks_rses[0] + i * rses_values_poss;
  }

  int32_t *cycle = (int32_t*) calloc(num_verts, sizeof(int32_t));
  int32_t *on_stack = (int32_t*) calloc(num_verts, sizeof(int32_t));
  int32_t *visited = (int32_t*) calloc(num_verts, sizeof(int32_t));
  int32_t** ori = init_orientation(num_verts, dim);
  // edge_map maps edge indices 0..(num_edges-1) to pairs (v,p) where v
  // is a vertex with 0 in the p location; this represents the edge connecting v
  // and v ^ (1 << p).
  struct vertexPos *edge_map = init_edge_map(num_edges, num_verts, dim, ori);

  set_orientation_to_allforward(edge_map, num_verts, dim, ori);

  unsigned __int128 num_codes;

  int32_t num_edges_to_try = num_edges;
#if WILDISSOURCE
  num_edges_to_try -= dim;
#endif
  num_codes = ((__int128)1LL) << num_edges_to_try;

  uint64_t num_acyclic = 0;

#if REPORTPROGRESS
  time_t start_time = time(NULL);
  uint64_t report_interval = num_codes;
  int32_t power_adj = 0;
  switch(dim) {
  case 3:
    report_interval = num_codes / 10;
    break;
  case 4:
    report_interval = num_codes / 100;
    break;
  case 5:
    report_interval = 1 << 20;
    power_adj = 50;
    break;
  }

  int64_t num_codes_adj = 1LL << (num_edges_to_try - power_adj);


#endif

  __int128 code_ind = ((__int128)0LL);


  // MAIN LOOP

  while (code_ind < num_codes) {

#if (VERBOSE >= 3)
    printf("Trying code %lld\n",code_ind);
#endif
#if REPORTPROGRESS
    if ((code_ind % report_interval) == 0) {
      time_t curr_time = time(NULL);
      int64_t time_elapsed = difftime(curr_time,start_time);
      double progress = ((double) code_ind)/num_codes_adj;
      int64_t total_time = (time_elapsed << (num_edges_to_try - power_adj)) / (1+code_ind);
      printf("  Time elapsed: %lld sec, Progress: %.8f * 2^-%d, Est total time: %lld * 2^%d sec \n",time_elapsed,progress,power_adj,total_time,power_adj);
    }
#endif
    int32_t found_cyc = 0;
    found_cyc = has_cycle(cycle, on_stack, visited, num_verts, dim, ori);

#if (VERBOSE >= 2)
    if (found_cyc > 0) {
#if REPORTCYCLE
      printf("============================================\n");
      printf("HAS CYCLE: ");
      for (int32_t i = found_cyc-1; i >= 0; i--) {
	print_binary(dim, cycle[i]);
	printf(" ");
      }
      printf("\n");
      print_orientation_adjlist(num_verts, dim, ori); 
#endif
    } else {
      printf("============================================\n");
      print_orientation_adjlist(num_verts, dim, ori); 
    } 
#endif

    if (found_cyc == 0) { // Acyclic orientation
      num_acyclic++;
      int32_t rse_count = count_rse(num_verts, dim, ori);
      int32_t sink_count = count_sinks(num_verts, dim, ori);
      ori_count_by_sinks_rses[sink_count][rse_count]++;
#if (VERBOSE >= 2)
      printf("RSEs: %d, Sinks: %d\n",rse_count,sink_count);
#endif
    }
    int32_t offset = 0;

    code_ind++;

    if (code_ind < num_codes) {
      offset = __builtin_ctzll(code_ind);
#if WILDISSOURCE
      offset += dim; // never change the first dim edges
#endif
      // flip the orientation of edge indexed by offset
      struct vertexPos vp = edge_map[offset];
      ori[vp.vert][vp.pos] ^= 1;
      ori[vp.vert ^ (1 << vp.pos)][vp.pos] ^= 1;
    }
  }

  printf("====================================================\n");
  printf("                   DIMENSION: %d                    \n",dim);
  printf("====================================================\n");
  printf("Total number of orientations: %llu\n",num_codes);
  printf("Number of acyclic orientations: %llu\n",num_acyclic);
  printf("Number of acyclic orientations with each (#RSEs,#Sinks)\n");
  printf("RSEs  |");
  for (int32_t sink_count = 0; sink_count < sinks_values_poss; sink_count++) {
    printf("\t%d",sink_count);
  }
  printf("\tSinks \n");
  printf("------|-----------------------------------------------------------------------\n");
  for (int32_t rse_count = 0; rse_count < rses_values_poss; rse_count++) {
    printf("%5d |",rse_count);
    for (int32_t sink_count = 0; sink_count < sinks_values_poss; sink_count++) {
      printf("\t%lld",ori_count_by_sinks_rses[sink_count][rse_count]);
    }
    printf("\n");
  }


  free(cycle);
  free(visited);
  free(on_stack);
  free(ori_count_by_sinks_rses[0]);
  free(ori_count_by_sinks_rses);
  free_orientation(ori);
  return 0;
}


