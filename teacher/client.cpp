
#include <iostream>
#include <cstring> // For memset()

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#define CLOSE_SOCKET(s) closesocket(s)
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#define CLOSE_SOCKET(s) close(s)
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#endif

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    SOCKET client_socket;
    sockaddr_in server_addr, sender_addr;
    char buffer[BUFFER_SIZE];

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed!" << std::endl;
        return EXIT_FAILURE;
    }
#endif

    // Create UDP socket
    client_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (client_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed!" << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    // Enable SO_REUSEADDR to allow multiple clients to bind
    int reuse = 1;
    if (setsockopt(client_socket, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
        std::cerr << "setsockopt(SO_REUSEADDR) failed!" << std::endl;
        CLOSE_SOCKET(client_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    // Enable SO_BROADCAST to receive broadcast messages
    int broadcastEnable = 1;
    if (setsockopt(client_socket, SOL_SOCKET, SO_BROADCAST, (char*)&broadcastEnable, sizeof(broadcastEnable)) == SOCKET_ERROR) {
        std::cerr << "setsockopt(SO_BROADCAST) failed!" << std::endl;
        CLOSE_SOCKET(client_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    // Configure client address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bind socket
    if (bind(client_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Binding failed!" << std::endl;
        CLOSE_SOCKET(client_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    std::cout << "UDP Client listening on port " << PORT << std::endl;

    socklen_t sender_addr_size = sizeof(sender_addr);

    while (true) {
        memset(buffer, 0, BUFFER_SIZE);

        // Receive broadcast message
        int bytes_received = recvfrom(client_socket, buffer, BUFFER_SIZE, 0, (struct sockaddr*)&sender_addr, &sender_addr_size);
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';
            std::cout << "Received: " << buffer << std::endl;
        }
    }

    CLOSE_SOCKET(client_socket);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
