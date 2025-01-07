cd /home/grips/cryomon

tail --lines=1500 textlog.dat > textlog_recent.dat

cat plot_grips_cryo.txt | gnuplot
cat plot_grips_cryo_recent.txt | gnuplot
#scp -P 36867 temp.jpeg brentm@apollo.ssl.berkeley.edu:/home/brentm/public_html
#scp -P 36867 temp_recent.jpeg brentm@apollo.ssl.berkeley.edu:/home/brentm/public_html
#scp -P 36867 textlog_recent.dat brentm@apollo.ssl.berkeley.edu:/home/brentm/public_html
scp temp.jpeg mops@128.32.13.93:/raid/logs/GRIPS
scp temp_recent.jpeg mops@128.32.13.93:/raid/logs/GRIPS
scp textlog_recent.dat mops@128.32.13.93:/raid/logs/GRIPS
