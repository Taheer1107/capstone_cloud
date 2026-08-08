import hashlib

# Function to generate SHA-256 hash
def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Function to build Merkle Tree
def build_merkle_tree(transactions):
    print("Transactions:")
    for t in transactions:
        print(t)

    # Step 1: hash all transactions (leaf nodes)
    leaves = [sha256(tx) for tx in transactions]
    print("\nLeaf hashes:")
    for h in leaves:
        print(h)

    tree = leaves[:]

    # Step 2: build tree
    while len(tree) > 1:
        temp = []

        # If odd number → duplicate last
        if len(tree) % 2 != 0:
            tree.append(tree[-1])

        print("\nCurrent level:")
        for h in tree:
            print(h)

        for i in range(0, len(tree), 2):
            combined = tree[i] + tree[i+1]
            parent = sha256(combined)
            temp.append(parent)

        tree = temp

    print("\nMerkle Root:", tree[0])
    return tree[0]

# Function to verify transaction
def verify_transaction(transaction, merkle_root, transactions):
    print("\nVerifying transaction:", transaction)

    if transaction not in transactions:
        print("Transaction not found!")
        return False

    new_root = build_merkle_tree(transactions)

    if new_root == merkle_root:
        print("Transaction is VALID")
        return True
    else:
        print("Transaction is INVALID")
        return False


# ------------------ MAIN PROGRAM ------------------

transactions = [
    "Alice pays Bob $10",
    "Charlie pays Dave $5",
    "Eve pays Frank $10"
]

root = build_merkle_tree(transactions)

# Verify a transaction
verify_transaction("Alice pays Bob $10", root, transactions)