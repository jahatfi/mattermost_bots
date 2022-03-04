grep Dm pt_log.txt  | sort | uniq -c | sort -k1nr -k2
echo "======================================="
grep Dm pt_log.txt | cut -f 1-2 -d " "   | sort -k1 -k3 | uniq -c | sort -k1nr -k2
