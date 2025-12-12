| Type      | Can Delete? | Can Grow? | Memory Usage        | Best Use Case                                           |
|-----------|-------------|-----------|---------------------|---------------------------------------------------------|
| Standard  | No          | No        | Low (1x)            | Web Crawlers, weak passwords lists.                     |
| Counting  | Yes         | No        | High (4x)           | Tracking active connections, frequency counts.          |
| Scalable  | No          | Yes       | Medium              | Databases where total item count is unknown.            |
| Cuckoo    | Yes         | No        | Low (Similar to Std)| General purpose replacement for Bloom (e.g., in Redis). |