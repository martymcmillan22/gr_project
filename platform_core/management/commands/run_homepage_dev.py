import shutil
import signal
import socket
import subprocess
import sys
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Run Django and Vite dev servers together for the homepage app."

    def add_arguments(self, parser):
        parser.add_argument("--django-host", default="127.0.0.1")
        parser.add_argument("--django-port", default="8000")
        parser.add_argument("--vite-host", default="127.0.0.1")
        parser.add_argument("--vite-port", default="5173")

    def handle(self, *args, **options):
        if not shutil.which("npm"):
            raise CommandError("npm is not available on PATH. Install Node.js first.")

        base_dir = Path(settings.BASE_DIR)
        frontend_dir = base_dir / "frontend_homepage"
        if not frontend_dir.exists():
            raise CommandError(f"Frontend folder not found: {frontend_dir}")

        django_host = options["django_host"]
        django_port = int(options["django_port"])
        vite_host = options["vite_host"]
        vite_port = int(options["vite_port"])

        django_in_use = self._is_port_in_use(django_host, django_port)
        vite_in_use = self._is_port_in_use(vite_host, vite_port)
        if django_in_use or vite_in_use:
            next_django = self._next_available_port(django_host, django_port + 1)
            next_vite = self._next_available_port(vite_host, vite_port + 1)
            conflicts = []
            if django_in_use:
                conflicts.append(f"Django port {django_host}:{django_port} is already in use")
            if vite_in_use:
                conflicts.append(f"Vite port {vite_host}:{vite_port} is already in use")

            suggestion = (
                "Use: "
                f"python manage.py run_homepage_dev --django-host {django_host} --django-port {next_django} "
                f"--vite-host {vite_host} --vite-port {next_vite}"
            )
            raise CommandError("; ".join(conflicts) + ". " + suggestion)

        vite_cmd = [
            "npm",
            "run",
            "dev",
            "--",
            "--host",
            vite_host,
            "--port",
            str(vite_port),
        ]
        django_cmd = [
            sys.executable,
            "manage.py",
            "runserver",
            f"{django_host}:{django_port}",
        ]

        self.stdout.write(self.style.SUCCESS("Starting Vite dev server..."))
        vite_proc = subprocess.Popen(vite_cmd, cwd=frontend_dir)

        try:
            self.stdout.write(self.style.SUCCESS("Starting Django dev server..."))
            self.stdout.write(
                f"Homepage URL: http://{django_host}:{django_port}/homepage/ | "
                f"Vite URL: http://{vite_host}:{vite_port}/"
            )
            env = os.environ.copy()
            env["HOMEPAGE_VITE_DEV_SERVER"] = f"http://{vite_host}:{vite_port}"
            subprocess.call(django_cmd, cwd=base_dir, env=env)
        finally:
            if vite_proc.poll() is None:
                self.stdout.write("Stopping Vite dev server...")
                vite_proc.terminate()
                try:
                    vite_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    vite_proc.send_signal(signal.SIGKILL)

    def _is_port_in_use(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                return True
        return False

    def _next_available_port(self, host, start_port):
        port = start_port
        while self._is_port_in_use(host, port):
            port += 1
        return port
