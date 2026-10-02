/* Hardware-free validation of native MemFd crop framing and RGB conversion. */
#include "pipewire_capture.c"
#include <assert.h>
int main(void) {
  (void)capture_main;
  int output[2]; assert(pipe(output) == 0);
  assert(fcntl(output[1], F_SETFL, O_NONBLOCK) == 0);
  int memory = memfd_create("companion-test", MFD_CLOEXEC);
  assert(memory >= 0 && ftruncate(memory, 8) == 0);
  const uint8_t pixels[] = {10,20,30,0,40,50,60,0};
  assert(write(memory, pixels, sizeof(pixels)) == 8);
  struct spa_chunk chunk = {.offset=0, .size=8, .stride=8};
  struct spa_data data = {.type=SPA_DATA_MemFd, .flags=SPA_DATA_FLAG_READABLE | SPA_DATA_FLAG_MAPPABLE,
      .fd=memory, .maxsize=8, .chunk=&chunk};
  struct spa_buffer spa = {.n_datas=1, .datas=&data};
  struct pw_buffer buffer = {.buffer=&spa};
  struct probe probe = {.have_format=1, .stream_output_fd=output[1]};
  probe.video.format=SPA_VIDEO_FORMAT_BGRx;
  probe.video.size.width=2; probe.video.size.height=1;
  assert(stream_frame_crop(&probe, &buffer, 1, 123) == 1);
  uint8_t frame[22]; assert(read(output[0], frame, sizeof(frame)) == 22);
  const uint8_t header[] = {'D','C','P','F',0,2,0,1};
  const uint8_t rgb[] = {30,20,10,60,50,40};
  assert(memcmp(frame, header, 8) == 0);
  assert(memcmp(frame+16, rgb, 6) == 0);
  assert(frame[15] == 123);
  chunk.stride=1;
  assert(stream_frame_crop(&probe, &buffer, 2, 124) == 0);
  stop_requested=1;
  assert(write_all(output[1], pixels, sizeof(pixels)) == -1);
  close(memory); close(output[0]); close(output[1]);
  puts("MemFd crop, RGB framing, bounds and interrupted write passed");
  return 0;
}
