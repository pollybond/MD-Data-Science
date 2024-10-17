workspace {
    name "BlaBlaCar"
    description "Сервис поиска попутчиков"

    !identifiers hierarchical

    model {
        user = person "Пользователь" {
            description "Пользователь приложения"
        }

        blablacar = softwareSystem "BlaBlaCar" {
            description "Система для поиска и организации поездок"

            webApp = container "Web-приложение" {
                description "Позволяет пользователям взаимодействовать с сервисом через браузер"
                technology "React, JavaScript"
            }

            apiGateway = container "API Gateway" {
                description "Обеспечивает доступ к бизнес-логике"
                technology "Node.js, Express"
            }

            userService = container "User Service" {
                description "Сервис управления пользователями"
                technology "Java Spring Boot"
            }

            routeService = container "Route Service" {
                description "Сервис управления маршрутами"
                technology "Java Spring Boot"
            }

            tripService = container "Trip Service" {
                description "Сервис управления поездками"
                technology "Java Spring Boot"
            }

            userDB = container "База данных пользователей" {
                description "Хранит информацию о пользователях"
                technology "PostgreSQL"
            }

            routeDB = container "База данных маршрутов" {
                description "Хранит информацию о маршрутах и поездках"
                technology "MongoDB"
            }

            tripDB = container "База данных поездок" {
                description "Хранит информацию о поездках"
                technology "MongoDB"
            }

            // Взаимодействие пользователя с системой
            user -> webApp "Использует для взаимодействия"
            webApp -> apiGateway "Запросы к API"
            apiGateway -> userService "Запросы на управление пользователями" "HTTPS"
            apiGateway -> routeService "Запросы на управление маршрутами" "HTTPS"
            apiGateway -> tripService "Запросы на управление поездками" "HTTPS"

            userService -> userDB "Чтение/Запись данных пользователей" "JDBC"
            routeService -> routeDB "Чтение/Запись маршрутов" "JDBC"
            tripService -> tripDB "Чтение/Запись поездок" "JDBC"

            // Основные сценарии использования
            user -> webApp "Создание нового пользователя"
            webApp -> apiGateway "POST /users"
            apiGateway -> userService "POST /users"
            userService -> userDB "INSERT INTO users"

            user -> webApp "Поиск пользователя по логину"
            webApp -> apiGateway "GET /users?login={login}"
            apiGateway -> userService "GET /users?login={login}"
            userService -> userDB "SELECT * FROM users WHERE login={login}"

            user -> webApp "Поиск пользователя по маске имени и фамилии"
            webApp -> apiGateway "GET /users?name={name}&surname={surname}"
            apiGateway -> userService "GET /users?name={name}&surname={surname}"
            userService -> userDB "SELECT * FROM users WHERE name LIKE {name} AND surname LIKE {surname}"

            user -> webApp "Создание маршрута"
            webApp -> apiGateway "POST /routes"
            apiGateway -> routeService "POST /routes"
            routeService -> routeDB "INSERT INTO routes"

            user -> webApp "Получение маршрутов пользователя"
            webApp -> apiGateway "GET /users/{userId}/routes"
            apiGateway -> routeService "GET /users/{userId}/routes"
            routeService -> routeDB "SELECT * FROM routes WHERE userId={userId}"

            user -> webApp "Создание поездки"
            webApp -> apiGateway "POST /trips"
            apiGateway -> tripService "POST /trips"
            tripService -> tripDB "INSERT INTO trips"

            user -> webApp "Подключение пользователей к поездке"
            webApp -> apiGateway "POST /trips/{tripId}/users"
            apiGateway -> tripService "POST /trips/{tripId}/users"
            tripService -> tripDB "UPDATE trips SET users = users + {userId} WHERE tripId={tripId}"

            user -> webApp "Получение информации о поездке"
            webApp -> apiGateway "GET /trips/{tripId}"
            apiGateway -> tripService "GET /trips/{tripId}"
            tripService -> tripDB "SELECT * FROM trips WHERE tripId={tripId}"
        }
    }
    
    views {
        themes default

        systemContext blablacar {
            include *
            autolayout lr
        }

        container blablacar {
            include *
            autolayout lr
        }

        dynamic blablacar "createUser" "Создание нового пользователя" {
            user -> blablacar.webApp "Создаёт нового пользователя"
            blablacar.webApp -> blablacar.apiGateway "POST /users"
            blablacar.apiGateway -> blablacar.userService "POST /users"
            blablacar.userService -> blablacar.userDB "INSERT INTO users"
            autolayout lr
        }

        dynamic blablacar "findUserByLogin" "Поиск пользователя по логину" {
            user -> blablacar.webApp "Ищет пользователя по логину"
            blablacar.webApp -> blablacar.apiGateway "GET /users?login={login}"
            blablacar.apiGateway -> blablacar.userService "GET /users?login={login}"
            blablacar.userService -> blablacar.userDB "SELECT * FROM users WHERE login={login}"
            autolayout lr
        }

        dynamic blablacar "findUserByName" "Поиск пользователя по маске имени и фамилии" {
            user -> blablacar.webApp "Ищет пользователя по имени и фамилии"
            blablacar.webApp -> blablacar.apiGateway "GET /users?name={name}&surname={surname}"
            blablacar.apiGateway -> blablacar.userService "GET /users?name={name}&surname={surname}"
            blablacar.userService -> blablacar.userDB "SELECT * FROM users WHERE name LIKE {name} AND surname LIKE {surname}"
            autolayout lr
        }

        dynamic blablacar "createRoute" "Создание нового маршрута" {
            user -> blablacar.webApp "Создаёт новый маршрут"
            blablacar.webApp -> blablacar.apiGateway "POST /routes"
            blablacar.apiGateway -> blablacar.routeService "POST /routes"
            blablacar.routeService -> blablacar.routeDB "INSERT INTO routes"
            autolayout lr
        }

        dynamic blablacar "getRoutes" "Получение маршрутов пользователя" {
            user -> blablacar.webApp "Запрашивает маршруты"
            blablacar.webApp -> blablacar.apiGateway "GET /users/{userId}/routes"
            blablacar.apiGateway -> blablacar.routeService "GET /users/{userId}/routes"
            blablacar.routeService -> blablacar.routeDB "SELECT * FROM routes WHERE userId={userId}"
            autolayout lr
        }

        dynamic blablacar "createTrip" "Создание новой поездки" {
            user -> blablacar.webApp "Создаёт новую поездку"
            blablacar.webApp -> blablacar.apiGateway "POST /trips"
            blablacar.apiGateway -> blablacar.tripService "POST /trips"
            blablacar.tripService -> blablacar.tripDB "INSERT INTO trips"
            autolayout lr
        }

        dynamic blablacar "joinTrip" "Подключение пользователей к поездке" {
            user -> blablacar.webApp "Подключается к поездке"
            blablacar.webApp -> blablacar.apiGateway "POST /trips/{tripId}/users"
            blablacar.apiGateway -> blablacar.tripService "POST /trips/{tripId}/users"
            blablacar.tripService -> blablacar.tripDB "UPDATE trips SET users = users + {userId} WHERE tripId={tripId}"
            autolayout lr
        }

        dynamic blablacar "getTrip" "Получение информации о поездке" {
            user -> blablacar.webApp "Запрашивает информацию о поездке"
            blablacar.webApp -> blablacar.apiGateway "GET /trips/{tripId}"
            blablacar.apiGateway -> blablacar.tripService "GET /trips/{tripId}"
            blablacar.tripService -> blablacar.tripDB "SELECT * FROM trips WHERE tripId={tripId}"
            autolayout lr
        }

        theme default
    }
}
