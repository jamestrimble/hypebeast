import random
import signal
import sys

random.seed(1)

sigterm_received = False
def sigterm_handler(_signo, _stack_frame):
    global sigterm_received
    print "c SIGTERM"
    sigterm_received = True
signal.signal(signal.SIGTERM, sigterm_handler)

class Bag:
    def __init__(self, bag_id, parent_id):
        self.id = bag_id
        self.parent_id = parent_id
        self.hyperedge_ids = []

    def copy(self):
        bag = Bag(self.id, self.parent_id)
        bag.hyperedge_ids = [he_id for he_id in self.hyperedge_ids]
        return bag

class HyperEdge:
    def __init__(self, hyperedge_id, vertices):
        self.id = hyperedge_id
        self.vertex_set = set(vertices)
        self.vertex_set_as_list = list(vertices)

    def __repr__(self):
        return "HE {} {}".format(self.id, self.vertex_set)

lines = [line.strip().split() for line in sys.stdin.readlines()]
lines = [line for line in lines if len(lines) > 0 and line[0] != "c"]

p_line = lines[0]
num_vertices = int(p_line[2])
num_hyperedges = int(p_line[3])

lines = [[int(token) for token in line] for line in lines[1:]]

hyperedges = {line[0]: HyperEdge(line[0], line[1:]) for line in lines}

vtx_to_number_of_appearances = [0] * (num_vertices + 1)
for he in hyperedges.values():
    for v in he.vertex_set:
        vtx_to_number_of_appearances[v] += 1
for he in hyperedges.values():
    he.score = min(vtx_to_number_of_appearances[v] for v in he.vertex_set)

def show_bags(bags):
    for bag in bags:
        print "bag {}   parent {}   edge_count {}   edges {} {}".format(bag.id, bag.parent_id, len(bag.hyperedge_ids),
                [hyperedges[he_id].vertex_set_as_list for he_id in bag.hyperedge_ids],
                ", ".join(sorted("\\{"+", ".join(str(x) for x in hyperedges[he_id].vertex_set_as_list)+"\\}" for he_id in bag.hyperedge_ids)))
    print

def attempt_move_to_child(bag, root_bag,
        root_hyperedges_that_do_not_overlap_a_previous_child, vertices_in_current_child_bag, scoring_system):
    best_score = (99999999, 0, 0)
    best_he_id = -1
    for he_id in root_hyperedges_that_do_not_overlap_a_previous_child:
#        score = len(hyperedges[he_id].vertex_set - vertices_in_current_child_bag)
        main_score = 0
        for v in hyperedges[he_id].vertex_set_as_list:
            if not vertices_in_current_child_bag[v]:
                main_score += 1
#                if score == best_score:
#                    break
        if len(bag.hyperedge_ids) == 0 and scoring_system == 0:
            score = (0, 0)
        else:
            score = (main_score, -len(hyperedges[he_id].vertex_set_as_list), hyperedges[he_id].score)
        if score < best_score:
            best_score = score
            best_he_id = he_id
            if score == 0:
                break
    if best_he_id != -1:
        bag.hyperedge_ids.append(best_he_id)
        for w in hyperedges[best_he_id].vertex_set:
            vertices_in_current_child_bag[w] = True
#        vertices_in_current_child_bag |= hyperedges[best_he_id].vertex_set
        root_bag.hyperedge_ids.remove(best_he_id)
        root_hyperedges_that_do_not_overlap_a_previous_child.remove(best_he_id)
        return True
    return False

def move_to_child_bags(root_bag, child_bags, max_number_of_he_in_child_bag, scoring_system):
    i = 0
    root_hyperedges_that_do_not_overlap_a_previous_child = list(root_bag.hyperedge_ids)
    while True:
        vertices_in_current_child_bag = [False] * (num_vertices + 1)
        if len(child_bags) == i:
            child_bags.append(Bag(child_bags[-1].id + 1, 1))
        while True:
            made_a_change = attempt_move_to_child(child_bags[i], root_bag,
                    root_hyperedges_that_do_not_overlap_a_previous_child, vertices_in_current_child_bag, scoring_system)
            if not made_a_change:
                break
            if len(child_bags[i].hyperedge_ids) == max_number_of_he_in_child_bag:
                break
        if len(child_bags[i].hyperedge_ids) == 0:
            break
        root_hyperedges_that_do_not_overlap_a_previous_child = [he_id for he_id in root_hyperedges_that_do_not_overlap_a_previous_child
                if not any(vertices_in_current_child_bag[w] for w in hyperedges[he_id].vertex_set_as_list)]
        i += 1

def vtx_is_extractable(v, num_uses_of_vtx, num_hyperedges_in_which_vtx_appears, bag):
    extractable = True
    he_ids = [he_id for he_id in bag.hyperedge_ids if v in hyperedges[he_id].vertex_set]
    for he_id in he_ids:
        for w in hyperedges[he_id].vertex_set:
            if w != v:
                num_uses_of_vtx[w] -= 1
                if num_uses_of_vtx[w] == 0  and num_hyperedges_in_which_vtx_appears[w] > 1:
                    extractable = False
    for he_id in he_ids:
        for w in hyperedges[he_id].vertex_set:
            if w != v:
                num_uses_of_vtx[w] += 1
    return extractable

def split_away_individual_hyperedges(bag, all_bags, num_uses_of_vtx, num_hyperedges_in_which_vtx_appears):
    used_vertices = [v for v in range(1, num_vertices+1) if num_uses_of_vtx[v]]
    for v in sorted(used_vertices):
        # Try to split away a set of hyperedges that contain all occurrences of some vertex v
        if num_uses_of_vtx[v] > 1 and num_uses_of_vtx[v] == num_hyperedges_in_which_vtx_appears[v] and vtx_is_extractable(
                                                                    v, num_uses_of_vtx, num_hyperedges_in_which_vtx_appears, bag):
            he_ids = [he_id for he_id in bag.hyperedge_ids if v in hyperedges[he_id].vertex_set]
            if len(he_ids) < len(bag.hyperedge_ids):   # don't do this if it leaves the bag empty
                all_bags.append(Bag(all_bags[-1].id + 1, bag.id))
                for he_id in he_ids:
                    all_bags[-1].hyperedge_ids.append(he_id)
                    bag.hyperedge_ids.remove(he_id)
                    for w in hyperedges[he_id].vertex_set_as_list:
                        num_uses_of_vtx[w] -= 1

    i = 0
    while i < len(bag.hyperedge_ids) and len(bag.hyperedge_ids) > 1:
        he_id = bag.hyperedge_ids[i]
        hyperedge = hyperedges[he_id]
        if all((num_hyperedges_in_which_vtx_appears[v]==1 or num_uses_of_vtx[v] > 1) for v in hyperedge.vertex_set_as_list):
            all_bags.append(Bag(all_bags[-1].id + 1, bag.id))
            all_bags[-1].hyperedge_ids.append(he_id)
            del bag.hyperedge_ids[i]
            for v in hyperedge.vertex_set_as_list:
                num_uses_of_vtx[v] -= 1
        else:
            i += 1

def w_appears(w, bag):
    for he_id in bag.hyperedge_ids:
        if w in hyperedges[he_id].vertex_set:
            return True
    return False

def split_away_individual_hyperedges2(bag, all_bags, num_uses_of_vtx):
    vertex_locked_in_root_node = [False] * (num_vertices + 1)
    for he_id in list(bag.hyperedge_ids):
        if len(bag.hyperedge_ids) == 1:
            break
        hyperedge = hyperedges[he_id]
        moved_hyperedge = False
        ww = [v for v in hyperedge.vertex_set_as_list if num_uses_of_vtx[v] == 1]
        uu = [v for v in hyperedge.vertex_set_as_list if num_uses_of_vtx[v] != 1]
        if len(ww)==1 and not vertex_locked_in_root_node[ww[0]]:
            w = ww[0]
            for bag2 in all_bags[1:]:
                if w_appears(w, bag2):
                    for v in uu:
                        vertex_locked_in_root_node[v] = True
                    bag2.hyperedge_ids.append(he_id)
                    bag.hyperedge_ids.remove(he_id)
                    for v in hyperedge.vertex_set_as_list:
                        num_uses_of_vtx[v] -= 1
                    moved_hyperedge = True
                    break

def find_solution(max_number_of_he_in_child_bag, prev_best_score, scoring_system, first_pass):
    root_bag = Bag(1, -1)
    root_bag.hyperedge_ids = [he_id for he_id in hyperedges.keys()]
    random.shuffle(root_bag.hyperedge_ids)

    show_bags([root_bag])

    child_bags = [Bag(2, 1)]

    move_to_child_bags(root_bag, child_bags, max_number_of_he_in_child_bag, scoring_system)

    if (len(child_bags[-1].hyperedge_ids) == 0):
        del child_bags[-1]

    all_bags_original = [root_bag] + child_bags
    best_score = max(len(bag.hyperedge_ids) for bag in all_bags_original)
    best_all_bags = all_bags_original

    show_bags(all_bags_original)

    for i in range(1):
        if sigterm_received:
            break
        all_bags = [bag.copy() for bag in all_bags_original]
        random.shuffle(all_bags[0].hyperedge_ids)
        num_hyperedges_in_which_vtx_appears = [0] * (num_vertices + 1)
        for he in hyperedges.values():
            for v in he.vertex_set_as_list:
                num_hyperedges_in_which_vtx_appears[v] += 1
        for bag in all_bags[:]:
            if bag != all_bags[0] and len(bag.hyperedge_ids) <= len(all_bags[0].hyperedge_ids):
                continue
    #        bag.hyperedge_ids.sort(key=lambda he_id: len(hyperedges[he_id].vertex_set))
            num_uses_of_vtx = [0] * (num_vertices + 1)
            for he_id in bag.hyperedge_ids:
                for v in hyperedges[he_id].vertex_set:
                    num_uses_of_vtx[v] += 1
            if bag == all_bags[0]:
                split_away_individual_hyperedges2(bag, all_bags, num_uses_of_vtx)
            split_away_individual_hyperedges(bag, all_bags, num_uses_of_vtx, num_hyperedges_in_which_vtx_appears)
#            if len(bag.hyperedge_ids) > min(prev_best_score, best_score):
#                break
            show_bags(all_bags)
        score = max(len(bag.hyperedge_ids) for bag in all_bags)
        if score < best_score:
            best_score = score
            best_all_bags = all_bags
        if best_score > prev_best_score + 1 and i > 3:
            break
        if best_score > prev_best_score and i > 10:
            break

    return best_score, best_all_bags

best_score = 999999999
best_bags = []
score_by_m = []
best_m = -1
#for m in range(1, num_hyperedges):
#    score, bags = find_solution(m, 999999, 0, True)
#    score_by_m.append((score, m))
##    print "c score ", score
#    if score < best_score:
#        best_bags = bags
#        best_score = score
#        best_m = m
#    if sigterm_received:
#        break
#
#score_by_m.sort()
#best_m_values = [x[1] for x in sorted(score_by_m)[:10]]
#
#for i in range(10):
#    for m in best_m_values:
#        score, bags = find_solution(m, best_score, i % 2, False)
##        print "c score ", score
#        if score < best_score:
#            best_bags = bags
#            best_score = score
#            best_m = m
#        if sigterm_received:
#            break

for i in range(1):
    m = 3
    score, bags = find_solution(m, best_score, i % 2, False)
#    print "c score ", score
    if score < best_score:
        best_bags = bags
        best_score = score
    if sigterm_received:
        break

print "c best score ", best_score

for bag in best_bags:
    print "c BAG", bag.id, bag.parent_id, len(bag.hyperedge_ids)

print "s htd {} {} {} {}".format(len(best_bags), best_score, num_vertices, num_hyperedges)

vertex_used = [False] * (num_vertices + 1)
for bag in best_bags:
    for he_id in bag.hyperedge_ids:
        for v in hyperedges[he_id].vertex_set:
            vertex_used[v] = True
unbagged_vertices = set()
for i in range(1, num_vertices + 1):
    if not vertex_used[i]:
        unbagged_vertices.add(i)

for bag in best_bags:
    involved_vv = set()
    for he_id in bag.hyperedge_ids:
        involved_vv = involved_vv | set(hyperedges[he_id].vertex_set)
    if bag.id == 1:
        involved_vv = involved_vv | unbagged_vertices
    print "b {} {}".format(bag.id, " ".join(str(x) for x in sorted(list(involved_vv))))

# Tree edges
for bag in best_bags:
    if bag.id > 1:
        print "{} {}".format(bag.parent_id, bag.id)

for bag in best_bags:
    for he_id in bag.hyperedge_ids:
        print "w {} {} 1".format(bag.id, he_id)
