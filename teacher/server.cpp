
#include <iostream>
#include <cstring> // For memset()
#include <string>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#define CLOSE_SOCKET(s) closesocket(s)
#define SLEEP(ms) Sleep(ms)
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#define CLOSE_SOCKET(s) close(s)
#define SLEEP(ms) usleep((ms) * 1000) // Convert milliseconds to microseconds
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#endif

#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    SOCKET server_socket;
    sockaddr_in server_addr, broadcast_addr;
    char buffer[BUFFER_SIZE];

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed!" << std::endl;
        return EXIT_FAILURE;
    }
#endif

    // Create UDP socket
    server_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (server_socket == INVALID_SOCKET) {
        std::cerr << "Socket creation failed!" << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    int reuse = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, (char*)&reuse, sizeof(reuse)) == SOCKET_ERROR) {
        std::cerr << "setsockopt(SO_REUSEADDR) failed!" << std::endl;
        CLOSE_SOCKET(server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    int broadcastEnable = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_BROADCAST, (char*)&broadcastEnable, sizeof(broadcastEnable)) == SOCKET_ERROR) {
        std::cerr << "setsockopt(SO_BROADCAST) failed!" << std::endl;
        CLOSE_SOCKET(server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    // Configure server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bind socket
    if (bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        std::cerr << "Binding failed!" << std::endl;
        CLOSE_SOCKET(server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    std::cout << "UDP Server broadcasting on port " << PORT << std::endl;

    memset(&broadcast_addr, 0, sizeof(broadcast_addr));
    broadcast_addr.sin_family = AF_INET;
    broadcast_addr.sin_port = htons(PORT);

    // Set broadcast address (Modify as per your network)
    if (inet_pton(AF_INET, "192.168.1.255", &broadcast_addr.sin_addr) <= 0) {
        std::cerr << "Invalid broadcast address!" << std::endl;
        CLOSE_SOCKET(server_socket);
#ifdef _WIN32
        WSACleanup();
#endif
        return EXIT_FAILURE;
    }

    while (true) {
        std::string message = "Broadcast message from server!";
        strncpy_s(buffer, message.c_str(), BUFFER_SIZE);

        // Send broadcast message
        if (sendto(server_socket, buffer, strlen(buffer), 0, (struct sockaddr*)&broadcast_addr, sizeof(broadcast_addr)) == SOCKET_ERROR) {
            std::cerr << "Broadcast failed!" << std::endl;
        }
        else {
            std::cout << "Broadcasted: " << buffer << std::endl;
        }

        SLEEP(5000); // Sleep 5 seconds
    }

    CLOSE_SOCKET(server_socket);
#ifdef _WIN32
    WSACleanup();
#endif

    return 0;
}
