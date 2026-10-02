/* MIT. Decktation Companion: desktop-user ScreenCast client, no game input. */
#define _GNU_SOURCE
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include "pipewire_capture.c"

#define PORTAL "org.freedesktop.portal.Desktop"
#define PORTAL_PATH "/org/freedesktop/portal/desktop"
#define SCREENCAST "org.freedesktop.portal.ScreenCast"
struct request { const char *path; GVariant *result; guint response; gboolean done; };
static void response_cb(GDBusConnection *c, const gchar *sender, const gchar *path,
                        const gchar *iface, const gchar *signal_name, GVariant *params, gpointer data) {
  (void)c; (void)sender; (void)iface; (void)signal_name;
  struct request *r = data;
  if (!r->path || strcmp(path, r->path) != 0 || r->done) return;
  g_variant_get(params, "(u@a{sv})", &r->response, &r->result);
  r->done = TRUE;
}
static GVariant *request_call(GDBusConnection *bus, const char *method, GVariant *args) {
  struct request r = {0};
  guint subscription = g_dbus_connection_signal_subscribe(bus, PORTAL,
      "org.freedesktop.portal.Request", "Response", NULL, NULL,
      G_DBUS_SIGNAL_FLAGS_NONE, response_cb, &r, NULL);
  GError *error = NULL;
  GVariant *reply = g_dbus_connection_call_sync(bus, PORTAL, PORTAL_PATH, SCREENCAST,
      method, args, G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &error);
  if (error) { fprintf(stderr, "companion_portal_method=%s error_domain=%s error_code=%d\n", method, g_quark_to_string(error->domain), error->code); g_error_free(error); }
  if (!reply) { g_dbus_connection_signal_unsubscribe(bus, subscription); return NULL; }
  g_variant_get(reply, "(&o)", &r.path);
  double deadline = monotonic_seconds() + 30;
  while (!r.done && !stop_requested && monotonic_seconds() < deadline) {
    while (g_main_context_pending(NULL)) g_main_context_iteration(NULL, FALSE);
    g_usleep(10000);
  }
  if (!r.done) {
    GVariant *closed = g_dbus_connection_call_sync(bus, PORTAL, r.path,
        "org.freedesktop.portal.Request", "Close", NULL, NULL,
        G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
    if (closed) g_variant_unref(closed);
  }
  g_dbus_connection_signal_unsubscribe(bus, subscription);
  g_variant_unref(reply);
  fprintf(stderr, "companion_portal_method=%s completed=%d response=%u\n", method, r.done, r.response);
  if (!r.done || r.response != 0) { if (r.result) g_variant_unref(r.result); return NULL; }
  return r.result;
}
static void options_init(GVariantBuilder *b, const char *token) {
  g_variant_builder_init(b, G_VARIANT_TYPE_VARDICT);
  g_variant_builder_add(b, "{sv}", "handle_token", g_variant_new_string(token));
}
int main(int argc, char **argv) {
  if (geteuid() == 0) { fprintf(stderr, "companion_error=desktop_user_required\n"); return 2; }
  if (argc == 2 && strcmp(argv[1], "--check-runtime") == 0) return 0;
  if (argc != 1) return 2;
  signal(SIGTERM, on_signal); signal(SIGINT, on_signal);
  int output_fd = dup(STDOUT_FILENO);
  if (output_fd < 0 || dup2(STDERR_FILENO, STDOUT_FILENO) < 0) return 2;
  if (fcntl(output_fd, F_SETFL, O_NONBLOCK) < 0) { close(output_fd); return 2; }
  GDBusConnection *bus = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, NULL);
  if (!bus) { close(output_fd); return 3; }
  int result = 3, remote_fd = -1;
  char *session = NULL, *serial = NULL;
  GVariant *reply = NULL;
  GVariantBuilder opts;
  char token[64]; snprintf(token, sizeof(token), "decktation_%ld", (long)getpid());
  options_init(&opts, token);
  g_variant_builder_add(&opts, "{sv}", "session_handle_token", g_variant_new_string(token));
  reply = request_call(bus, "CreateSession", g_variant_new("(a{sv})", &opts));
  if (!reply) goto cleanup;
  if (!g_variant_lookup(reply, "session_handle", "s", &session) &&
      !g_variant_lookup(reply, "session_handle", "o", &session)) goto cleanup;
  if (!g_variant_is_object_path(session)) goto cleanup;
  g_variant_unref(reply); reply = NULL;
  snprintf(token, sizeof(token), "decktation_select_%ld", (long)getpid());
  options_init(&opts, token);
  g_variant_builder_add(&opts, "{sv}", "types", g_variant_new_uint32(1));
  g_variant_builder_add(&opts, "{sv}", "multiple", g_variant_new_boolean(FALSE));
  g_variant_builder_add(&opts, "{sv}", "cursor_mode", g_variant_new_uint32(1));
  reply = request_call(bus, "SelectSources", g_variant_new("(oa{sv})", session, &opts));
  if (!reply) goto cleanup;
  g_variant_unref(reply); reply = NULL;
  snprintf(token, sizeof(token), "decktation_start_%ld", (long)getpid());
  options_init(&opts, token);
  reply = request_call(bus, "Start", g_variant_new("(osa{sv})", session, "", &opts));
  if (!reply) goto cleanup;
  GVariant *streams = g_variant_lookup_value(reply, "streams", G_VARIANT_TYPE("a(ua{sv})"));
  if (!streams || g_variant_n_children(streams) != 1) { if (streams) g_variant_unref(streams); goto cleanup; }
  guint32 node_id; GVariant *properties;
  g_variant_get_child(streams, 0, "(u@a{sv})", &node_id, &properties);
  GVariant *serial_value = g_variant_lookup_value(properties, "pipewire-serial", NULL);
  if (serial_value) {
    if (g_variant_is_of_type(serial_value, G_VARIANT_TYPE_UINT64))
      serial = g_strdup_printf("%" G_GUINT64_FORMAT, g_variant_get_uint64(serial_value));
    else if (g_variant_is_of_type(serial_value, G_VARIANT_TYPE_STRING))
      serial = g_variant_dup_string(serial_value, NULL);
    g_variant_unref(serial_value);
  }
  g_variant_unref(properties); g_variant_unref(streams);
  g_variant_unref(reply); reply = NULL;
  GUnixFDList *fds = NULL;
  g_variant_builder_init(&opts, G_VARIANT_TYPE_VARDICT);
  reply = g_dbus_connection_call_with_unix_fd_list_sync(bus, PORTAL, PORTAL_PATH,
      SCREENCAST, "OpenPipeWireRemote", g_variant_new("(oa{sv})", session, &opts),
      G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &fds, NULL, NULL);
  if (!reply) goto cleanup;
  gint32 handle; g_variant_get(reply, "(h)", &handle);
  if (fds) { remote_fd = g_unix_fd_list_get(fds, handle, NULL); g_object_unref(fds); }
  if (remote_fd < 0 || stop_requested) goto cleanup;
  portal_serial = serial;
  fprintf(stderr, "companion_selector=%s\n", serial ? "serial" : "numeric");
  char fd_text[32], node_text[32], output_text[32];
  snprintf(fd_text, sizeof(fd_text), "%d", remote_fd);
  snprintf(node_text, sizeof(node_text), "%u", node_id);
  snprintf(output_text, sizeof(output_text), "%d", output_fd);
  char *capture_args[] = {"companion-capture", "--fd", fd_text, "--node-id", node_text,
      "--stream-output-fd", output_text, "--stream-interval-ms", "5000",
      "--timeout-ms", "2147483647", NULL};
  result = capture_main(11, capture_args);
cleanup:
  if (reply) g_variant_unref(reply);
  if (remote_fd >= 0) close(remote_fd);
  if (session) {
    GVariant *closed = g_dbus_connection_call_sync(bus, PORTAL, session,
        "org.freedesktop.portal.Session", "Close", NULL, NULL,
        G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
    if (closed) g_variant_unref(closed);
  }
  g_free(serial); g_free(session); g_object_unref(bus); close(output_fd);
  if (result) fprintf(stderr, "companion_error=capture_unavailable\n");
  return result;
}
