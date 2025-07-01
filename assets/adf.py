class DynamicHashTable:
    def __init__(self, initial_capacity=8):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [[] for _ in range(self.capacity)]
    
    def hash(self, key):
        return hash(key) % self.capacity
    
    def insert(self, key, value):
        index = self.hash(key)
        bucket = self.buckets[index]
        
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self.size += 1

        if self.load_factor() > 0.75:
            self.resize()

    def get(self, key):
        index = self.hash(key)
        bucket = self.buckets[index]
        print(index)

        for k, v in bucket:
            if k == key:
                return v
        return None

    def delete(self, key):
        index = self.hash(key)
        bucket = self.buckets[index]

        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.size -= 1
                return True
        return False

    def load_factor(self):
        return self.size / self.capacity

    def resize(self):
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        self.size = 0

        for bucket in old_buckets:
            for key, value in bucket:
                self.insert(key, value)

# Example usage:
table = DynamicHashTable()
table.insert("name", "Majd")
table.insert("mane", "Majd")
table.insert("age", 18)
print(hash('age')%table.capacity , hash('name')%table.capacity)
print(table.get("age"))  # Output: Majd


print(table.buckets)
