# Muestra de rendimiento de Organigrama

`organigrama_rendimiento_300.og` contiene datos completamente sintéticos:

- 1 secretario;
- 9 directores;
- 45 coordinadores, jefes o encargados;
- 245 personas de apoyo administrativo;
- 299 conexiones jerárquicas.

La muestra es determinista y se puede regenerar desde la raíz del proyecto:

```powershell
python -m App_Organigrama.samples.generate_performance_sample
```

También se puede cambiar la ruta o la semilla:

```powershell
python -m App_Organigrama.samples.generate_performance_sample `
  --output C:\temp\organigrama_300.og `
  --seed 12345
```

Después se abre el archivo `.og` normalmente desde Organigrama.
