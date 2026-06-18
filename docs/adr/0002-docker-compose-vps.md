# ADR 0002: Docker Compose als primaerer VPS-Deployment-Pfad

## Status

Accepted

## Kontext

Das System soll auf einem klassischen VPS self-hostbar sein und Postgres sowie
Qdrant mitbringen.

## Entscheidung

Docker Compose ist der Standardpfad fuer Deployment. K3s-Manifeste werden als
sekundaere Option bereitgestellt.

## Konsequenzen

- Ein VPS braucht nur Docker und das Compose Plugin.
- Persistente Volumes werden direkt in `docker-compose.yml` verwaltet.
- K3s kann spaeter fuer Cluster-Setups ausgebaut werden.
