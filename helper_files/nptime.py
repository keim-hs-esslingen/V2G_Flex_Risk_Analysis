#!/usr/bin/env python
"""Non-Pedantic Time
=================

.. moduleauthor:: Thomas Grenfell Smith <thomathom@gmail.com>

Python's :mod:`datetime` module has many uses, but it has a difficulty: you
can't do any arithmetic with :class:`datetime.time`.  Only with
:class:`datetime.datetime`.  Now, there are good reasons for this:  "What time
will it be, 24 hours from now" has a lot of corner cases, including daylight
savings time, leap seconds, historical timezone changes, and so on.  But
sometimes you really *do* need the simple case.  Sometimes the perfect is the
enemy of the good.  And that's why you have this module.  This module will allow
you to cocoon yourself in the comforting illusion that, in 24 hours, it will be
the same time as it is right now.

And what freedom this illusion gives you!  You can add a
:class:`datetime.timedelta` object to an :mod:`nptime` object, and it works! It
will cycle around 24 hours, like modular arithmetic.  You can ask "what time
comes 1 day and 36 minutes after 12:24 pm?" and it will let you know: 1:00 pm.
How lovely!

Anyway, please use this module.  It will
be convenient.  But don't use it when talking about concrete time, time in
a particular place, or anything like that.  In fact, it doesn't even notice
:class:`datetime.tzinfo` objects right now.  Good luck.

.. note::
    You can find the newest version at https://github.com/tgs/nptime .  You can
    find online documentation at http://tgs.github.com/nptime/ .  The package
    is available for download from PyPi:  `easy_install nptime`.
    This software is licensed under the `3-clause BSD License
    <https://raw.github.com/tgs/nptime/master/LICENSE.txt>`_.

"""
#import datetime
from datetime import *
import math

class nptime(time):
    """nptime - a non-pedantic time object

    Inherits from :class:`datetime.time`.  You can't do arithmetic with that
    class, but with ``nptime`` you can:

    * Add a :class:`datetime.timedelta` to an :class:`nptime` (commutative),
        resulting in another ``nptime``
    * Subtract a ``timedelta`` from an ``nptime``, resulting in an
        ``nptime``
    * Subtract an ``nptime`` from another ``nptime``, resulting in a
        ``timedelta``

    You can use the class methods :func:`from_timedelta` and :func:`from_time`
    to construct an ``nptime`` from those ``datetime`` classes.  You can use the
    :func:`to_timedelta` instance method to construct a ``timedelta`` from an
    ``nptime``.

    I can't figure out a reason you'd want to add two times together without
    using ``timedelta`` objects, but if someone requests that, I'm happy to
    include it.

    ``nptime`` is `naive` about time zones.  I think this is the only way that
    makes sense, since days are only 24 hours long in an abstract sense.  But
    if you want to see a different system, pull requests are welcome..."""

    _std_date = date(year=1000, month=1, day=1)

    @classmethod
    def from_time(cls, other):
        """Construct an :class:`nptime` object from a :class:`datetime.time`

        .. note::
            This *ignores* the :class:`datetime.tzinfo` that may be part
            of the ``time`` object.
        """
        return cls(other.hour, other.minute, other.second, other.microsecond)

    @classmethod
    def from_timedelta(cls, other):
        """Construct an :class:`nptime` object from a :class:`datetime.timedelta`.

        The ``timedelta`` is taken to be the amount of time since midnight."""
        return cls() + other

    def to_timedelta(self):
        """Construct a :class:`timedelta` object from an :class:`nptime`.  The
        timedelta gives the number of seconds (and microseconds) since
        midnight."""
        return timedelta(hours=self.hour, minutes=self.minute,
                seconds=self.second, microseconds=self.microsecond)

    def __add__(self, other):
        """Add nptime and timedelta, returning an nptime"""
        self_dt = datetime.combine(self._std_date, self)
        sum = self_dt + other
        return self.from_time(sum.time())

    def __radd__(self, other):
        """Add timedelta and nptime"""
        return self + other

    def __sub__(self, other):
        """
        Subtract timedelta or nptime from nptime.

        You can subtract two nptimes from each other, giving
        the timedelta between them.  You can also subtract
        a timedelta from an nptime, giving an earlier nptime.
        """
        if isinstance(other, self.__class__):
            # Two nptimes, so find the delta between them
            return self.to_timedelta() - other.to_timedelta()
        else:
            # Assume the other is a timedelta; delegate to adding
            return self + (-other)

def delta_to_float(time):
    time_new = time.days*3600*24+time.seconds*1000000+time.microseconds
    return time_new/1000000

def floor_timedelta(divider, divisor):
    new_time = math.floor((divider.seconds*1000000+divider.microseconds)/divisor)
    new_timedelta = timedelta(microseconds=new_time)
    return new_timedelta

def delta_to_nptime(time):
    time = time - datetime.timedelta(days = time.days)
    in_seconds = time.total_seconds()
    hours = in_seconds/3600
    minutes = hours/60
    seconds = minutes/60
    microseconds = seconds/1000000
    return nptime(hour = int(hours), minute = int(minutes), second = int(seconds), microsecond=int(microseconds))