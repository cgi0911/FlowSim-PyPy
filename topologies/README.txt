Formats of nodes and links descriptions:

1. The file name of nodes and links descriptions shall be 'nodes.csv' and 'links.csv', respectively.
   The two files shall reside in the same folder, with folder name set to topology name.

2. Both nodes.csv and links.csv are comma-separated CSV files. The first line shall be header line
   that provides column names. All non-numeric fields shall be enclosed by double quotation marks.
   Integers must contain integral digits only. For floating point numbers, at least one decimal
   digits should be explicitly shown in the CSV file.

3. Required columns of nodes.csv:
   "name", "n_hosts", "table_size"
   Though we are able to override n_hosts and table_size in config.py, they are still required in
   nodes.csv. All other columns are optional.

4. Required columns of links.csv:
   "node1", "node2", "bw"
   Though we are able to override bw in config.py, the column is still required in links.csv.
   Note that the links are undirectional.