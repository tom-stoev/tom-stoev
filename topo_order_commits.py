import os, sys, zlib
def get_topo_ordered_commits(commit_nodes, root_hashes):
    order = []
    visited = set()
    temp_stack = []
    commit_nodes = (commit_nodes)
    stack = sorted(list(root_hashes))
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)

        while len(temp_stack) > 0 and (commit_nodes[v].commit_hash not in commit_nodes[temp_stack[len(temp_stack)-1]].children):
            g = temp_stack.pop()
            order.append(g)
        temp_stack.append(v)
        for c in sorted(commit_nodes[v].children):
            if c in visited:
                continue
            stack.append(c)
    for i in range(0, len(temp_stack)):
        order.append(temp_stack.pop())
    return (order)
            

def getBranches(path, add):
    os.chdir(path)
    files = os.listdir()
    branches = []
    names = []
    accum = ''
    accum+=add
    # print(accum)
    for i in range(0, len(files)):
        length = len(files[i])
        extract = files[i]
        if os.path.isfile(path + extract):
            branches.append(accum+extract)
            with open(path + str(extract), 'r') as f:
                data = f.read()
                data = data.strip()
            branches.append(data)
        else:
            branches += getBranches(path+extract+'/', accum+extract+'/')
    return branches

class CommitNode:
    def __init__(self, commit_hash):
        self.commit_hash = str(commit_hash)
        self.parents = set()
        self.children = set()


def build_commit_graph(git_dir, branches):
    os.chdir(git_dir)
    commit_nodes = {}
    root_hashes = set()
    visited = set()
    deleteSet = []
    local_branch_heads=[]
    for i in range(0, len(branches)):
        if i%2==1:
            local_branch_heads.append(branches[i])
    stack = sorted(local_branch_heads)
    while stack:
        commit_hash = stack.pop()
        if commit_hash in visited:
            continue
        visited.add(commit_hash)
        check_record = -1
        if commit_hash not in commit_nodes:
            commit_node = CommitNode(commit_hash)
            commit_nodes[commit_hash] = commit_node
                
                    
        #search objects for hash 
        files = os.listdir()
        for i in range(0, len(files)):
            prefix = commit_hash[0]+commit_hash[1]
            if files[i] == prefix:
                os.chdir(git_dir + prefix)
                f = os.listdir()
                for i in range(0, len(f)):
                    find_comm = commit_hash[2:40]
                    if f[i] == find_comm:
                        compressed = open(git_dir+prefix+'/'+f[i], 'rb').read()
                        decompressed = zlib.decompress(compressed)
                        break
                break
        count_Parents = decompressed.count(b'parent')
        if count_Parents > 0:
            for i in range(0, count_Parents):
                x = decompressed.index(b'parent')
                parent = decompressed[x+7:x+47]
                commit_nodes[commit_hash].parents.add(str(parent)[2:42])
                decompressed = decompressed[x+47:]
            for i in sorted(commit_nodes[commit_hash].parents):
                if i not in visited:
                    stack.append(i)
                check = 0
                if i in commit_nodes:
                    commit_nodes[i].children.add(commit_hash)
                else:
                    newNode = CommitNode(i)
                    newNode.children.add(commit_hash)
                    commit_nodes[i] = newNode
        else:
            root_hashes.add(commit_hash)
        os.chdir(git_dir)
    return root_hashes, commit_nodes

def make_head_to_branches(branches):
    branches = branches
    branch_dict = {}
    i=0
    while i < len(branches):
        if branches[i+1] in branch_dict:
            branch_dict[branches[i+1]].append(branches[i])
        else: 
            branch_dict.update({branches[i+1]: [branches[i]]})
        i+=2
    return branch_dict

def print_topo_ordered_commits_with_branch_names(commit_nodes, topo_ordered_commits, head_to_branches): 
    jumped = False
    for i in range(len(topo_ordered_commits)):
        commit_hash = topo_ordered_commits[i] 
        if jumped:
            jumped = False
            sticky_hash = ' '.join(sorted(commit_nodes[commit_hash].children)) 
            print(f'={sticky_hash}')
        branches = sorted(head_to_branches[commit_hash]) if commit_hash in head_to_branches else [] 
        print(commit_hash + (' ' + ' '.join(branches) if branches else ''))
        if i+1 < len(topo_ordered_commits) and topo_ordered_commits[i+1] not in commit_nodes[commit_hash].parents: 
            jumped = True
            sticky_hash = ' '.join(sorted(commit_nodes[commit_hash].parents)) 
            print(f'{sticky_hash}=\n')

        




def main():
    files = os.listdir()
    path = os.getcwd()
    while path!='/':
        path = os.getcwd()
        for i in range(0, len(files)):
            if files[i] == '.git':
                path_length = len(path)
                path_objects = path
                if path[path_length-1] != '/':
                    path+='/.git/refs/heads/'
                    path_objects+='/.git/objects/'
                else:
                    path+='.git/refs/heads/'
                    path_objects+='.git/objects/'
                branches = getBranches(path, '')
                root_hashes, commit_graph = build_commit_graph(path_objects, branches)
                order = get_topo_ordered_commits(commit_graph, root_hashes)
                head_to_branches = make_head_to_branches(branches)
                print_topo_ordered_commits_with_branch_names(commit_graph, order, head_to_branches)
                return 0
        spl = path.split('/')
        newpath = ''
        for i in range(0, len(spl)-1):
            newpath+=spl[i]+'/'
        os.chdir(newpath)
        files = os.listdir()
    print("Not inside a Git repository")
    return 1
if __name__ == "__main__":
    main()
