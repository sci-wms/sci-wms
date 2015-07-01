from django.http import HttpResponse


def from_dataframe(request, df):
    if request.GET['info_format'] == 'text/csv':
        response = HttpResponse(content_type='text/csv')
        response.write(df.to_csv(index=False, float_format='%.4f'))
    elif request.GET['info_format'] == 'text/tsv':
        response = HttpResponse(content_type='text/tsv')
        response.write(df.to_csv(sep='\t', index=False, float_format='%.4f'))
    elif request.GET['info_format'] == 'application/json':
        response = HttpResponse(content_type='application/json')
        response.write(df.to_json(orient='records'))

    return response
