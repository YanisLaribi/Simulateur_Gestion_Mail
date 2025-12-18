"""\
GLO-2000 Travail pratique 4 - Client 2025
Noms et numéros étudiants:
-
-
-
"""

import argparse
import getpass
import json
import re
import socket
import sys

import glosocket
import gloutils



class Client:
    """Client pour le serveur mail @glo2000.ca 2025."""

    def __init__(self, destination: str) -> None:
        """
        Prépare et connecte le socket du client `_socket`.

        Prépare un attribut `_username` pour stocker le nom d'utilisateur
        courant. Laissé vide quand l'utilisateur n'est pas connecté.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((destination, gloutils.APP_PORT))
        except glosocket.GLOSocketError:
            sys.exit(1)

        self._username = ""

    def _register(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_REGISTER`.

        Si la création du compte s'est effectuée avec succès, l'attribut
        `_username` est mis à jour, sinon l'erreur est affichée.
        """
        # entrer les nom, mdp, mess
        name = input("Entrer un nom d'utilisateur: ")
        pwd = getpass.getpass("Entrez votre mot de passe: ")
        # preparer le message contenant les infos de l'user
        mess = json.dumps(gloutils.GloMessage(
            header=gloutils.Headers.AUTH_REGISTER,
            payload=gloutils.AuthPayload(username=name, password=pwd)
        ))
        # envoyer le message
        try:
            glosocket.send_mesg(self._socket, mess)
            res = json.loads(glosocket.recv_mesg(self._socket))
        except glosocket.GLOSocketError:
            print("Erreur: erreur lors de l'envoi/reception du message\n")
        # si creation avec succes => mettre a jour nom
        # sinon erreur
        if res["header"] == gloutils.Headers.OK:
            self._username = name.lower() #Jai modifie cela du code de Tiavintsoa, parce qu'on stock les deux tout en minuscule dans le serveur
            print("Compte créé avec succès!\n")#Ajout fait par Yanis

        elif res["header"] == gloutils.Headers.ERROR:
            print(res["payload"].get("error_message"))

    def _login(self) -> None:
        """
        Demande un nom d'utilisateur et un mot de passe et les transmet au
        serveur avec l'entête `AUTH_LOGIN`.

        Si la connexion est effectuée avec succès, l'attribut `_username`
        est mis à jour, sinon l'erreur est affichée.
        """
        # recuperer nom, mdp
        name = input("Entrer un nom d'utilisateur: ")
        pwd = getpass.getpass("Entrez votre mot de passe: ")
        # preparer mess
        mess = json.dumps(gloutils.GloMessage(
            header=gloutils.Headers.AUTH_LOGIN,
            payload=gloutils.AuthPayload(username=name, password=pwd)
        ))
        # envoyer message
        try:
            glosocket.send_mesg(self._socket, mess)
            res = json.loads(glosocket.recv_mesg(self._socket))
        except glosocket.GLOSocketError:
            print("Erreur: erreur lors de l'envoi/reception du message")
            return

        # si creation avec succes => mettre a jour nom
        # sinon erreur
        if res["header"] == gloutils.Headers.OK:
            self._username = name
        elif res["header"] == gloutils.Headers.ERROR:
            print(res["payload"].get("error_message"))

    def _quit(self) -> None:
        """
        Préviens le serveur de la déconnexion avec l'entête `BYE` et ferme le
        socket du client.
        """
        mess = gloutils.GloMessage(
            header=gloutils.Headers.BYE
        )
        glosocket.send_mesg(self._socket, json.dumps(mess))
        self._socket.close()

    def _read_email(self) -> None:
        """
        Demande au serveur la liste de ses courriels avec l'entête
        `INBOX_READING_REQUEST`.

        Affiche la liste des courriels puis transmet le choix de l'utilisateur
        avec l'entête `INBOX_READING_CHOICE`.

        Affiche le courriel à l'aide du gabarit `EMAIL_DISPLAY`.

        S'il n'y a pas de courriel à lire, l'utilisateur est averti avant de
        retourner au menu principal.
        """
        # envoyer une requete pour recuperer les emails
        glosocket.send_mesg(self._socket, json.dumps(
            gloutils.GloMessage(
                header=gloutils.Headers.INBOX_READING_REQUEST
            )
        ))
        # recuperer le message envoyer par le serveur
        rep = json.loads(glosocket.recv_mesg(self._socket))
        liste = rep["payload"].get("email_list")  # liste des emails

        if len(liste) == 0:
            print("Vous n'avez recu aucun email\n")
        else:
            # afficher tous les emails
            for email in liste:
                print(email)
            # recuperer le choix de l'email a afficher
            choice = input(f"Entrer votre choix [1-{len(liste)}]")
            # envoyer le choix au serveur
            glosocket.send_mesg(self._socket, json.dumps(gloutils.GloMessage(
                header=gloutils.Headers.INBOX_READING_CHOICE,
                payload=gloutils.EmailChoicePayload(choice=choice)
            )))
            # recuperer le EmailContentPayload dans le message envoyer par le serveur
            email = json.loads(glosocket.recv_mesg(self._socket))["payload"]
            # afficher l'email sous le format EMAIL_DISPLAY
            print(gloutils.EMAIL_DISPLAY.format(
                sender=email.get("sender"),
                to=email.get("destination"),
                subject=email.get("subject"),
                date=email.get("date"),
                body=email.get("content")
            ))

    def _send_email(self) -> None:
        """
        Demande à l'utilisateur respectivement:
        - l'adresse email du destinataire,
        - le sujet du message,
        - le corps du message.

        La saisie du corps se termine par un point seul sur une ligne.

        Transmet ces informations avec l'entête `EMAIL_SENDING`.
        """
        # demander l'email de destination tant que c'est pas encore valide
        while True:
            dest = input("Adresse de destination: ")
            if re.search(r"(^[a-zA-Z0-9_\.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-\.]+$)", dest):
                break
        # le sujet de l'email
        sujet = input("Sujet: ")
        print("Message (terminer par une ligne ne contenant qu'un '.'):")
        # recuperer le contenu du message
        # tant que c'est pas une ligne contenant un '.'
        # on continue de recuperer
        contenu = ""
        while True:
            ligne = input()
            if ligne == ".":
                break
            contenu = contenu + ligne + "\n"
        # recuperer la date lors de l'envoi
        date = gloutils.get_current_utc_time()

        # envoyer toutes ces informations au serveur
        # pour l'email du sender, je l'ai forcer a username@glo2000.ca
        glosocket.send_mesg(self._socket, json.dumps(gloutils.GloMessage(
            header=gloutils.Headers.EMAIL_SENDING,
            payload=gloutils.EmailContentPayload(
                sender=f"{self._username}@{gloutils.SERVER_DOMAIN}",
                destination=dest,
                subject=sujet,
                content=contenu,
                date=date
            )
        ))
                            )

        rep = json.loads(glosocket.recv_mesg(self._socket))
        if rep["header"] == gloutils.Headers.OK:
            print("Email envoyé avec succès!\n")
        else:
            print(rep["payload"].get("error_message"))

    def _check_stats(self) -> None:
        """
        Demande les statistiques au serveur avec l'entête `STATS_REQUEST`.

        Affiche les statistiques à l'aide du gabarit `STATS_DISPLAY`.
        """
        mess = gloutils.GloMessage(
            header=gloutils.Headers.STATS_REQUEST
        )
        glosocket.send_mesg(self._socket, json.dumps(mess))

        rep = json.loads(glosocket.recv_mesg(self._socket))
        # afficher les statistique du dossier sous le format STATS_DISPLAY
        print(gloutils.STATS_DISPLAY.format(
            count=rep["payload"].get("count"),
            size=rep["payload"].get("size")
        ))

    def _logout(self) -> None:
        """
        Préviens le serveur avec l'entête `AUTH_LOGOUT`.

        Met à jour l'attribut `_username`.
        """
        try:
            glosocket.send_mesg(self._socket,json.dumps(
                gloutils.GloMessage(header=gloutils.Headers.AUTH_LOGOUT)
            ))
        except glosocket.GLOSocketError:
            print("Erreur: erreur lors de la deconnexion")
        self._username = ""

    def run(self) -> None:
        """Point d'entrée du client."""
        should_quit = False

        while not should_quit:
            if not self._username:
                # Authentication menu
                print(gloutils.CLIENT_AUTH_CHOICE)
                choice = input("Entrer votre choix: ")

                if choice == "1":
                    self._register()
                elif choice == "2":
                    self._login()
                elif choice == "3":
                    self._quit()
                    should_quit = 1
                else:
                    print("Entrer un nombre entre [1-3]")
            else:
                # Main menu
                print(gloutils.CLIENT_USE_CHOICES)
                choice = input("Entrer votre choix: ")

                if choice == "1":
                    self._read_email()
                elif choice == "2":
                    self._send_email()
                elif choice == "3":
                    self._check_stats()
                elif choice == "4":
                    self._logout()
                else:
                    print("Entrer un nombre entre [1-4]")


# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT
# NE PAS ÉDITER PASSÉ CE POINT


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--destination",
        action="store",
        dest="dest",
        required=True,
        help="Adresse IP/URL du serveur.",
    )
    args = parser.parse_args(sys.argv[1:])
    client = Client(args.dest)
    client.run()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
