#define NOMINMAX
#include <windows.h>
#include <atomic>
#include <thread>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include <algorithm>
#include <pybind11/pybind11.h>

namespace py = pybind11;

// Shared state
std::atomic<bool> running(false);
std::atomic<bool> paused(false);
std::atomic<int> interval_ms(5000);
std::thread worker;

HBITMAP screen_backup = nullptr;

int normalize_interval(int timer_ms)
{
    return std::max(1, timer_ms);
}

// Save the desktop before the memz starts.
void capture_screen()
{
    if (screen_backup)
    {
        DeleteObject(screen_backup);
        screen_backup = nullptr;
    }

    HWND hwnd = GetDesktopWindow();
    HDC hdc = GetWindowDC(hwnd);
    HDC memdc = CreateCompatibleDC(hdc);

    RECT r;
    GetWindowRect(hwnd, &r);

    int w = r.right - r.left;
    int h = r.bottom - r.top;

    screen_backup = CreateCompatibleBitmap(hdc, w, h);
    SelectObject(memdc, screen_backup);

    BitBlt(memdc, 0, 0, w, h, hdc, 0, 0, SRCCOPY);

    DeleteDC(memdc);
    ReleaseDC(hwnd, hdc);
}

// Put the saved desktop back.
void restore_screen()
{
    if (!screen_backup)
        return;

    HWND hwnd = GetDesktopWindow();
    HDC hdc = GetWindowDC(hwnd);
    HDC memdc = CreateCompatibleDC(hdc);

    RECT r;
    GetWindowRect(hwnd, &r);

    SelectObject(memdc, screen_backup);

    BitBlt(hdc, 0, 0, r.right - r.left, r.bottom - r.top, memdc, 0, 0, SRCCOPY);

    DeleteDC(memdc);
    ReleaseDC(hwnd, hdc);
    DeleteObject(screen_backup);
    screen_backup = nullptr;
}

// Main memz effect loop
void pieces_loop()
{
    HWND hwnd = GetDesktopWindow();
    HDC hdc = GetWindowDC(hwnd);

    RECT r;
    GetWindowRect(hwnd, &r);
    int screen_width = r.right - r.left;
    int screen_height = r.bottom - r.top;

    while (running)
    {
        if (!paused)
        {
            int x1 = std::rand() % std::max(1, screen_width - 100);
            int y1 = std::rand() % std::max(1, screen_height - 100);
            int x2 = std::rand() % std::max(1, screen_width - 100);
            int y2 = std::rand() % std::max(1, screen_height - 100);
            int width = std::rand() % 600;
            int height = std::rand() % 600;

            if (width < 50)
                width = 50;
            if (height < 50)
                height = 50;

            if (x1 + width > screen_width)
                width = std::max(1, screen_width - x1);
            if (y1 + height > screen_height)
                height = std::max(1, screen_height - y1);
            if (x2 + width > screen_width)
                x2 = std::max(0, screen_width - width);
            if (y2 + height > screen_height)
                y2 = std::max(0, screen_height - height);

            BitBlt(hdc, x1, y1, width, height, hdc, x2, y2, SRCCOPY);
        }

        int remaining_ms = normalize_interval(interval_ms.load());
        while (running && remaining_ms > 0)
        {
            const int sleep_chunk_ms = std::min(remaining_ms, 10);
            std::this_thread::sleep_for(std::chrono::milliseconds(sleep_chunk_ms));
            remaining_ms -= sleep_chunk_ms;

            const int updated_interval = normalize_interval(interval_ms.load());
            if (updated_interval < remaining_ms)
                remaining_ms = updated_interval;
        }
    }

    ReleaseDC(hwnd, hdc);
}

// Python-facing API
void start(int timer_ms = 5000)
{
    interval_ms = normalize_interval(timer_ms);

    if (running)
        return;

    std::srand(static_cast<unsigned int>(std::time(nullptr)));
    capture_screen();

    running = true;
    paused = false;
    worker = std::thread(pieces_loop);
}

void set_timer(int timer_ms)
{
    interval_ms = normalize_interval(timer_ms);
}

bool is_running()
{
    return running.load();
}

void pause()
{
    paused = true;
}

void resume()
{
    paused = false;
}

void stop()
{
    running = false;
    paused = false;

    if (worker.joinable())
        worker.join();

    restore_screen();
}

// Module exports
PYBIND11_MODULE(pieces, m)
{
    m.def("start", &start, py::arg("timer") = 5000,
          "Start the pieces effect for the memz with an optional timer interval in milliseconds.");
    m.def("is_running", &is_running, "Return whether the pieces effect for the memz is running.");
    m.def("pause", &pause, "Pause the pieces effect for the memz without clearing the screen.");
    m.def("resume", &resume, "Resume the pieces effect for the memz after pausing.");
    m.def("timer", &set_timer, py::arg("timer"),
          "Set the memz effect interval in milliseconds.");
    m.def("stop", &stop, "Stop the pieces effect for the memz and restore the screen.");
}
