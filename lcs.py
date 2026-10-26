def read_lines(path):
    with open(path, "r") as f:
        return f.read().splitlines()


def build_table(a, b):
    m = len(a)
    n = len(b)
    table = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])
    return table


def backtrack(a, b, table):
    i=len(a)
    j=len(b)
    pairs=[]
    while i>0 and j>0:
        if(a[i-1]==b[j-1]):
            pairs.append((i-1,j-1))
            i-=1
            j-=1
        elif(table[i-1][j]>=table[i][j-1]):
            i-=1
        else:
            j-=1
    return pairs[::-1]

if __name__ == "__main__":
    #Test1 small test from paper exercise
    a=['a','b','c','d']
    b=['a','b','e','d']
    table=build_table(a,b)
    print("LCS length: ",table[len(a)][len(b)])
    pairs=backtrack(a,b,table)
    print("LCS pairs: ",pairs)

    #Test2 sample
    base = read_lines("merge_optimizer\\samples\\set1_no_conflict\\base.txt")
    devA = read_lines("merge_optimizer\\samples\\set1_no_conflict\\devA.txt")
    dp = build_table(base, devA)
    print("Base vs DevA LCS length:", dp[len(base)][len(devA)])
    print("Pairs:", backtrack(base, devA, dp))