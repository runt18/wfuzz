usage='''\r\n
Interactive keyboard commands:\r\n
?: Show this help

p: Pause
s: Show stats
q: Cancel
'''

class Controller:
    def __init__(self, fuzzer, view):
	self._debug = False
	self.fuzzer = fuzzer
	self.view = view
	self.__paused = False

	self.view.dispatcher.subscribe(self.on_help, "?")
	self.view.dispatcher.subscribe(self.on_pause, "p")
	self.view.dispatcher.subscribe(self.on_stats, "s")
	self.view.dispatcher.subscribe(self.on_exit, "q")

    # dynamic keyboard bindings
    def on_exit(self, **event):
	self.fuzzer.genReq.stats.mark_end()
	self.fuzzer.cancel_job()
	#self.view.cancel_job()
	#self.view.cancel_job()

    def on_help(self, **event):
	print usage

    def on_pause(self, **event):
	self.__paused = not self.__paused
	if self.__paused:
	    self.fuzzer.pause_job()

	    if self._debug:
		print "\n=============== Paused =================="
		stats = self.fuzzer.stats()
		for k,v in stats.items():
		    print "{0!s}: {1!s}".format(k, v)
		print "\n========================================="
	else:
	    self.fuzzer.resume_job()

    def on_stats(self, **event):
	if self._debug:
	    fzstats = self.fuzzer.stats()

	    print "\nTotal items {0:d}, Backfed items {1:d}, HTTP reqs: {2:d}, Fuzzed items: {3:d}, Pending: {4:d} (Wait HTTP: {5:d}, Wait pre HTTP: {6:d}, Wait Workers: {7:d}, Wait processed: {8:d}). (MEM: {9:d})".format(fzstats['total'], \
		fzstats['backfed'], \
		fzstats['http_Processed'], \
		fzstats['Processed'], \
		fzstats['Pending'], \
		fzstats['http_Pending'], \
		fzstats['http_queue'], \
		fzstats['plugins_queue'], \
		fzstats['results_queue']
		)
	else:
	    pending = self.fuzzer.genReq.stats.total_req - self.fuzzer.genReq.stats.processed
	    summary = self.fuzzer.genReq.stats
	    summary.mark_end()
	    print "\nTotal requests: {0!s}\r".format(str(summary.total_req))
	    print "Pending requests: {0!s}\r".format(str(pending))

	    if summary.backfeed > 0:
		print "Processed Requests: {0!s} ({1:d} + {2:d})\r".format(str(summary.processed)[:8], (summary.processed - summary.backfeed), summary.backfeed)
	    else:
		print "Processed Requests: {0!s}\r".format((str(summary.processed)[:8]))
	    print "Filtered Requests: {0!s}\r".format((str(summary.filtered)[:8]))
	    req_sec = summary.processed/summary.totaltime if summary.totaltime > 0 else 0
	    print "Total time: {0!s}\r".format(str(summary.totaltime)[:8])
	    if req_sec > 0:
		print "Requests/sec.: {0!s}\r".format(str(req_sec)[:8])
		eta = pending/req_sec
		if eta > 60:
		    print "ET left min.: {0!s}\r\n".format(str(eta/60)[:8])
		else:
		    print "ET left sec.: {0!s}\r\n".format(str(eta)[:8])

