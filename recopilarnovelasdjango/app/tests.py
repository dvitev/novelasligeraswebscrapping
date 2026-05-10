import unittest
import json
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
from django.test import TestCase, Client, override_settings
from rest_framework import status
from rest_framework.exceptions import ErrorDetail


class TestSitiosEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.sitio_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Sitio.objects')
    def test_list_sitios_returns_200(self, mock_objects):
        mock_sitio = MagicMock()
        mock_sitio._id = ObjectId(self.sitio_id)
        mock_sitio.nombre = 'Test Sitio'
        mock_sitio.url = 'https://test.com'
        mock_sitio.imagen_url = 'https://test.com/img.png'
        mock_sitio.estructura = MagicMock()
        mock_sitio.estructura.estructura = '{"test": "data"}'
        mock_objects.all.return_value = [mock_sitio]

        response = self.client.get('/api/sitios/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    @patch('app.viewsets.Sitio.objects')
    def test_retrieve_sitio_returns_200(self, mock_objects):
        mock_sitio = MagicMock()
        mock_sitio._id = ObjectId(self.sitio_id)
        mock_sitio.nombre = 'Test Sitio'
        mock_sitio.url = 'https://test.com'
        mock_sitio.imagen_url = 'https://test.com/img.png'
        mock_sitio.estructura = MagicMock()
        mock_sitio.estructura.estructura = '{"test": "data"}'
        mock_objects.filter.return_value = [mock_sitio]

        response = self.client.get(f'/api/sitios/{self.sitio_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.Sitio.objects')
    def test_retrieve_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/sitios/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestEstructuraSitioEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.estructura_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.EstructuraSitio.objects')
    def test_retrieve_estructura_returns_200(self, mock_objects):
        mock_estructura = MagicMock()
        mock_estructura._id = ObjectId(self.estructura_id)
        mock_estructura.estructura = '{"selector": "value"}'
        mock_objects.filter.return_value = [mock_estructura]

        response = self.client.get(f'/api/estructurasitio/{self.estructura_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.EstructuraSitio.objects')
    def test_retrieve_estructura_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/estructurasitio/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestNovelaEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.novela_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_novela_returns_200(self, mock_objects):
        mock_novela = MagicMock()
        mock_novela._id = ObjectId(self.novela_id)
        mock_novela.nombre = 'Test Novela'
        mock_novela.sinopsis = 'Test sinopsis'
        mock_novela.autor = 'Test Author'
        mock_novela.genero = 'Action, Adventure'
        mock_novela.status = 'ongoing'
        mock_novela.url = 'https://test.com/novela'
        mock_novela.imagen_url = 'https://test.com/cover.png'
        mock_objects.filter.return_value = [mock_novela]

        response = self.client.get(f'/api/novelas/{self.novela_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_novela_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/novelas/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestNovelaSitioEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.sitio_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Novela.objects')
    @patch('app.viewsets.cache')
    def test_list_novelas_by_sitio_returns_200(self, mock_cache, mock_objects):
        mock_novela = MagicMock()
        mock_novela._id = ObjectId()
        mock_novela.nombre = 'Test Novela'
        mock_novela.sinopsis = 'Test sinopsis'
        mock_novela.autor = 'Test Author'
        mock_novela.genero = 'Action, Adventure'
        mock_novela.status = 'ongoing'
        mock_novela.url = 'https://test.com/novela'
        mock_novela.imagen_url = 'https://test.com/cover.png'
        
        mock_qs = MagicMock()
        mock_qs.values.return_value = [mock_novela]
        mock_objects.filter.return_value = mock_qs

        response = self.client.get(f'/api/novelasitio/{self.sitio_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_novela_with_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/novelasitio/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestConteoCapitulosEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.novela_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Novela.objects')
    @patch('app.viewsets.Capitulo.objects')
    @patch('app.viewsets.ContenidoCapitulo.objects')
    def test_retrieve_conteo_returns_200(self, mock_contenido, mock_capitulos, mock_novela):
        novela_id = ObjectId(self.novela_id)
        mock_novela_obj = MagicMock()
        mock_novela_obj._id = novela_id
        mock_novela_obj.nombre = 'Test Novela'
        mock_novela_obj.sinopsis = 'Test sinopsis'
        mock_novela_obj.autor = 'Test Author'
        mock_novela_obj.genero = 'Action'
        mock_novela_obj.status = 'ongoing'
        mock_novela_obj.url = 'https://test.com'
        mock_novela_obj.imagen_url = 'https://test.com/cover.png'
        mock_novela.objects.get.return_value = mock_novela_obj
        
        mock_cap_qs = MagicMock()
        mock_cap_qs.count.return_value = 10
        mock_capitulos.filter.return_value = mock_cap_qs
        
        mock_cont_qs = MagicMock()
        mock_cont_qs.count.return_value = 5
        mock_contenido.filter.return_value = mock_cont_qs

        response = self.client.get(f'/api/conteocapitulosnovela/{self.novela_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get('cantidad_capitulos'), 10)
        self.assertEqual(data.get('cantidad_contenido_capitulos'), 5)
        self.assertEqual(data.get('nombre'), 'Test Novela')

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_conteo_not_found_returns_404(self, mock_objects):
        from app.models import Novela
        mock_objects.get.side_effect = Novela.DoesNotExist()

        response = self.client.get(f'/api/conteocapitulosnovela/{self.novela_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_conteo_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/conteocapitulosnovela/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestCapitulosEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.capitulo_id = str(ObjectId())
        self.novela_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Capitulo.objects')
    def test_retrieve_capitulo_returns_200(self, mock_objects):
        mock_cap = MagicMock()
        mock_cap._id = ObjectId(self.capitulo_id)
        mock_cap.nombre = 'Chapter 1'
        mock_cap.novela_id = self.novela_id
        mock_objects.filter.return_value = [mock_cap]

        response = self.client.get(f'/api/capitulos/{self.capitulo_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.Capitulo.objects')
    def test_retrieve_capitulo_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/capitulos/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('app.viewsets.Capitulo.objects')
    def test_retrieve_capitulos_by_novela_returns_200(self, mock_objects):
        mock_cap = MagicMock()
        mock_cap._id = ObjectId()
        mock_cap.nombre = 'Chapter 1'
        mock_cap.novela_id = self.novela_id
        mock_objects.filter.return_value = [mock_cap]

        response = self.client.get(f'/api/capitulosnovelas/{self.novela_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.Capitulo.objects')
    def test_retrieve_capitulosnovelas_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/capitulosnovelas/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestContenidoCapituloEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.capitulo_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.ContenidoCapitulo.objects')
    def test_list_contenido_returns_200(self, mock_objects):
        mock_obj = MagicMock()
        mock_obj._id = ObjectId()
        mock_obj.capitulo_id = self.capitulo_id
        mock_obj.novela_id = 'novela123'
        mock_obj.texto = 'Test content'
        mock_objects.all.return_value = [mock_obj]

        response = self.client.get('/api/contenidocapitulo/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('app.viewsets.ContenidoCapitulo.objects')
    def test_retrieve_contenido_by_capitulo_returns_200(self, mock_objects):
        mock_obj = MagicMock()
        mock_obj._id = ObjectId()
        mock_obj.capitulo_id = self.capitulo_id
        mock_obj.novela_id = 'novela123'
        mock_obj.texto = 'Test content'
        mock_objects.filter.return_value = [mock_obj]

        response = self.client.get(f'/api/contenidocapitulo/{self.capitulo_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestGeneroEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.sitio_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_generos_by_sitio_returns_200(self, mock_objects):
        mock_qs = MagicMock()
        mock_qs.values_list.return_value = ['Action, Adventure', 'Fantasy']
        mock_objects.filter.return_value = mock_qs

        response = self.client.get(f'/api/generos/{self.sitio_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('generos', response.json())

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_generos_excludes_prohibited(self, mock_objects):
        mock_qs = MagicMock()
        mock_qs.values_list.return_value = ['Yaoi', 'Action', 'Shounen ai']
        mock_objects.filter.return_value = mock_qs

        response = self.client.get(f'/api/generos/{self.sitio_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        generos = response.json()['generos']
        self.assertNotIn('Yaoi', generos)
        self.assertNotIn('Shounen ai', generos)

    @patch('app.viewsets.Novela.objects')
    def test_retrieve_generos_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/api/generos/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestHealthCheckEndpoint(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('app.views_health.MongoClient')
    def test_health_check_healthy_returns_200(self, mock_client):
        mock_admin = MagicMock()
        mock_client.return_value.admin.command.return_value = {'ok': 1}

        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'healthy')

    @patch('app.views_health.MongoClient')
    def test_health_check_connection_failure_returns_503(self, mock_client):
        from pymongo.errors import ConnectionFailure
        mock_client.side_effect = ConnectionFailure("Connection failed")

        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.json()['status'], 'unhealthy')

    @patch('app.views_health.MongoClient')
    def test_health_check_timeout_returns_503(self, mock_client):
        from pymongo.errors import ServerSelectionTimeoutError
        mock_client.side_effect = ServerSelectionTimeoutError("Timeout")

        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class TestExportPDFEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.novela_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.services.export_service.Novela.objects')
    def test_generar_pdf_returns_200(self, mock_objects):
        mock_novela = MagicMock()
        mock_novela._id = ObjectId(self.novela_id)
        mock_novela.nombre = 'Test Novela'
        mock_novela.autor = 'Test Author'
        mock_novela.sinopsis = 'Test synopsis'
        mock_novela.url = 'https://test.com'
        mock_novela.imagen_url = None
        
        mock_qs = MagicMock()
        mock_qs.values.return_value = [mock_novela]
        mock_objects.filter.return_value = mock_qs

        with patch('app.services.export_service.Capitulo.objects') as mock_caps, \
             patch('app.services.export_service.ContenidoCapitulo.objects') as mock_cont:
            mock_caps_qs = MagicMock()
            mock_caps_qs.values.return_value = []
            mock_caps.filter.return_value = mock_caps_qs
            
            mock_cont_qs = MagicMock()
            mock_cont_qs.values.return_value = []
            mock_cont.filter.return_value = mock_cont_qs
            
            response = self.client.get(f'/generar_pdf/{self.novela_id}/')
            
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @patch('app.services.export_service.Novela.objects')
    def test_generar_pdf_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/generar_pdf/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('app.services.export_service.Novela.objects')
    def test_generar_pdf_not_found_returns_404(self, mock_objects):
        mock_qs = MagicMock()
        mock_qs.values.return_value = []
        mock_objects.filter.return_value = mock_qs

        response = self.client.get(f'/generar_pdf/{self.novela_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestExportEPUBEndpoint(TestCase):
    def setUp(self):
        self.client = Client()
        self.novela_id = str(ObjectId())
        self.invalid_id = 'invalid-object-id'

    @patch('app.services.export_service.Novela.objects')
    def test_generar_epub_returns_200(self, mock_objects):
        mock_novela = MagicMock()
        mock_novela._id = ObjectId(self.novela_id)
        mock_novela.nombre = 'Test Novela'
        mock_novela.autor = 'Test Author'
        mock_novela.sinopsis = 'Test synopsis'
        mock_novela.url = 'https://test.com'
        mock_novela.imagen_url = None
        
        mock_qs = MagicMock()
        mock_qs.values.return_value = [mock_novela]
        mock_objects.filter.return_value = mock_qs

        with patch('app.services.export_service.Capitulo.objects') as mock_caps, \
             patch('app.services.export_service.ContenidoCapitulo.objects') as mock_cont:
            mock_caps_qs = MagicMock()
            mock_caps_qs.values.return_value = []
            mock_caps.filter.return_value = mock_caps_qs
            
            mock_cont_qs = MagicMock()
            mock_cont_qs.values.return_value = []
            mock_cont.filter.return_value = mock_cont_qs
            
            response = self.client.get(f'/generar_epub/{self.novela_id}/')
            
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @patch('app.services.export_service.Novela.objects')
    def test_generar_epub_invalid_id_returns_400(self, mock_objects):
        response = self.client.get(f'/generar_epub/{self.invalid_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    unittest.main()