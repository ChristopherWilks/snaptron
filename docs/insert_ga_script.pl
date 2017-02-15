#!/usr/bin/perl

use strict;
use warnings;

my $ga_script=qq(
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
	    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
    m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
	    })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-90108023-1', 'auto');
    ga('send', 'pageview');
    </script>
);

while(my $line = <STDIN>)
{
	chomp($line);
	if($line =~ /^\s*<head>\s*$/)
	{
		print "$line\n$ga_script\n";
		next;
	}
	print "$line\n";
}
