""" Command line interface for creating changemaps of YATSM algorithm output
"""
import logging

import click

from . import options


logger = logging.getLogger('yatsm')


opt_table = click.option('--table',
                         type=str, default=None, show_default=True,
                         help='Extract data from this table')


opt_column = click.option('--column',
                          type=str, default=None, show_default=True,
                          help='Extract data from this column')


@click.group(short_help='Map change found by YATSM algorithm over time period')
@click.pass_context
def changemap(ctx):
    pass


@changemap.command(short_help="Date of first change")
@options.arg_config
@options.arg_start_date
@options.arg_end_date
@options.arg_output
@opt_table
@options.opt_bounds
@options.mapping_decorations
@options.opt_date_format
@options.opt_map_date_format
def first(ctx, config, start_date, end_date, output,
          table, bounds,
          driver, nodata, creation_options, force_overwrite,
          date_format, map_date_format):
    """ Date of first change
    """
    # TODO: make this an input...
    # TODO: mapping between
    #           * output band # and total # bands
    #           * result value mapping/transform function
    #           * also takes care of QA/QC
    attr_columns = ('break_day', )
    attr_funcs = (None, )

    import numpy as np
    import rasterio
    from yatsm.mapping import result_map
    # Get results, then pop first out to get geographic attrs.
    # Finally, return it back into result generator
    # TODO: limit query by extent somehow?
    # TODO: this should be more robust to first result being corrupt...
    results = config.find_results(**config.results)
    try:
        result, results = config.peak_results(results, table=table)
    except StopIteration:
        logger.error('Cannot find results')
        raise click.Abort()

    if not table:
        table = config.peak_table(result)[0]
        logger.info('Assuming you want table: "{0}"'.format(table))

    # TODO: manually specify extent (e.g., subset)
    #: BoundingBox: bounds, in geographic/projected "real" coordinates
    bounds = bounds or result.bounds
    logger.debug('Using bounds: {0!r}'.format(bounds))

    # TODO: allow window to come from arg, e.g., "srcwin"
    window = rasterio.windows.from_bounds(*bounds,
                                          transform=result.georef.transform,
                                          boundless=True)
    logger.debug('Calculated window as: {0!r}'.format(window))
    # Recalculate transform
    transform = rasterio.windows.transform(window, result.transform)

    kwds = {
        'driver': driver,
        'nodata': nodata,
        'dtype': np.int32,
        'count': len(attr_columns),  # TODO: qa/qc band may influence this
        'crs': result.georef.crs,
        'height': window[0][1] - window[0][0],
        'width': window[1][1] - window[1][0],
        'transform': rasterio.windows.transform(window, transform)
    }
    kwds.update(**creation_options)

    with rasterio.open(output, 'w', **kwds) as dst:
        out = np.full(dst.shape, dst.nodata, dst.dtypes[0])
        out = result_map(out, results, table, attr_columns,
                         attr_funcs=attr_funcs,
                         d_start=start_date, d_end=end_date)
        dst.write(out)
        print(dst.tags())
    logger.info('Complete')


@changemap.command(short_help="Date of last change")
@options.mapping_decorations
def last(ctx, driver, nodata, creation_options, force_overwrite):
    """ Date of last change
    """
    click.echo("Last change detected")


@changemap.command(short_help="Number of changes")
@options.mapping_decorations
def num(ctx, driver, nodata, creation_options, force_overwrite):
    """ Number of changes
    """
    click.echo("Number of changes")
