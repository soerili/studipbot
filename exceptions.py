class AliasError(Exception):
    def __init__(self, alias):
        self.alias = alias
        self.message = f'Der Alias {alias} wurde nicht in der Konfiguration gefunden. Wenn du ihn hinzufügen möchtest benutze bitte `!studip alias <Alias> <Modulnummer>`'
        super().__init__(self.message)


class DatabaseError(Exception):
    def __init__(self, user):
        self.user = user
        self.message = 'Ich habe deinen Benutzer nicht in der Datenbank gefunden, bitte trage dich über `!studip login` ein.'
        super().__init__(self.message)


class LoginError(Exception):
    def __init__(self, login):
        self.login = login
        self.message = f'Das Psswort für den Benutzer {login} scheint falsch zu sein. Bitte versuche es mit `!studip login` erneut.'
        super().__init__(self.message)


class ArgumentError(Exception):
    def __init__(self, command):
        self.command = command
        self.message = f'Bei der Benutzung von {command} wurde eine falsche Anzahl an Argumenten übergeben. \nWenn du dir nicht sicher bist, benutze `!studip` um dir die Benutzung von Befehlen anzuzeigen'
        super().__init__(self.message)


class ApiError(Exception):
    def __init__(self):
        super().__init__('Die Verbindung mit der API ist fehlgeschlagen. Entweder ist dein Passwort falsch, die API momentan nicht erreichbar oder du hast dieses Modul garnicht belegt.')