from matplotlib.testing.noseclasses import KnownFailureTest, \
     KnownFailureDidNotFailTest, ImageComparisonFailure
import sys
import nose
from matplotlib.cbook import get_sample_data
from matplotlib.testing.compare import compare_images

def knownfailureif(fail_condition, msg=None):
    # based on numpy.testing.dec.knownfailureif
    if msg is None:
        msg = 'Test known to fail'
    def known_fail_decorator(f):
        # Local import to avoid a hard nose dependency and only incur the
        # import time overhead at actual test-time.
        import nose
        def failer(*args, **kwargs):
            try:
                # Always run the test (to generate images).
                result = f(*args, **kwargs)
            except:
                if fail_condition:
                    raise KnownFailureTest(msg) # An error here when running nose means that you don't have the matplotlib.testing.noseclasses:KnownFailure plugin in use.
                else:
                    raise
            if fail_condition and fail_condition != 'indeterminate':
                raise KnownFailureDidNotFailTest(msg)
            return result
        return nose.tools.make_decorator(f)(failer)
    return known_fail_decorator

def image_comparison(baseline_images=None, tol=1e-3):
    if baseline_images is None:
        raise ValueError('baseline_images must be specified')
    def compare_images_decorator(func):
        def decorated_compare_images(*args,**kwargs):
            result = func(*args,**kwargs)
            for fname in baseline_images:
                actual = fname
                expected = get_sample_data('test_baseline_%s'%fname,
                                           asfileobj=False)
                err = compare_images( expected, actual, tol,
                                      in_decorator=True )
                if err:
                    raise ImageComparisonFailure(
                        'images not close: %(actual)s vs. %(expected)s '
                        '(RMS %(rms).3f)'%err)
            return result
        return nose.tools.make_decorator(func)(decorated_compare_images)
    return compare_images_decorator
