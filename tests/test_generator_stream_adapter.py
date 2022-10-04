import io
import shutil
import unittest

from runner.containers import GeneratorStreamAdapter


def sample_generator():
    yield b"Hello world.\n"
    yield b"x" * 100
    yield b"\n"


class TestGeneratorStreamAdapter(unittest.TestCase):
    def test_generator_stream_adapter(self):
        expected_output = b"".join(sample_generator())

        stream = GeneratorStreamAdapter(sample_generator())
        bio = io.BytesIO()
        shutil.copyfileobj(stream, bio)
        self.assertEqual(bio.getvalue(), expected_output)

        stream = GeneratorStreamAdapter(sample_generator())
        bio = io.BytesIO()
        shutil.copyfileobj(stream, bio, 5)
        self.assertEqual(bio.getvalue(), expected_output)
