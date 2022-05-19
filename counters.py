"""
 read and reset of hardware counters
"""
def reset_cntrs(self):
    """
     reset all counters
    """
    # reset tng counters as list
    for c in [self.dev_counter_01, self.dev_counter_07]:#self.cntrsList:
        self.reset_cntr(c)


def reset_cntr(self,dev):
    """
     resets counter to 0
    """
    dev.Reset()
    return

def read_cntr(self,dev):
    """
     reads a counter value
     return as float
    """
    return dev.read_attribute('Counts').value

def timer_read_sampletime(self, dev):
    """
     reads the current sampletime from tng counter
    """
    return dev.read_attribute('SampleTime').value

def timer_set_sampletime(self,dev, sampletime):
    """
     sets a sampletime on tng counter
    """
    dev.write_attribute('SampleTime', float(sampletime))
    return

def timer_start(self,dev):
    """
     starts a counter device
    """
    dev.Start()
    return
def timer_stop(self, dev):
    """
     stops a counter device
    """
    dev.Stop()
    return