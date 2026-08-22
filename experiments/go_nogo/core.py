"""
VARUNA Go/No-Go Experiment — Core Physics Engine
=================================================
Pure NumPy/SciPy implementation of:
  1. Particle advection (forward & backward) under synthetic currents
  2. Backward ensemble with perturbed forcing
  3. Φ(x, y, t) origin probability field construction
  4. Synthetic vessel track generation
  5. Path-integral scoring of tracks against Φ
  6. Posterior computation with latent-source hypothesis

No OpenDrift dependency. We graduate to OpenDrift in Week 2 with real CMEMS data.
"""

import numpy as np
from scipy.stats import gaussian_kde
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import warnings

# ─── Constants ───────────────────────────────────────────────────────────────

EARTH_RADIUS_M = 6_371_000
DEG_TO_M = 111_320  # approximate meters per degree latitude
KNOTS_TO_MS = 0.5144  # knots to m/s


# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class CurrentField:
    """
    Synthetic ocean current field.
    For the go/no-go experiment, we use a spatially uniform but temporally
    varying current — good enough to test the method, not the data.
    """
    base_u: float  # base eastward velocity (m/s)
    base_v: float  # base northward velocity (m/s)
    rotation_period_hours: float = 48.0  # period of directional oscillation
    rotation_amplitude_deg: float = 15.0  # max angular deviation

    def velocity_at(self, t_hours: float) -> Tuple[float, float]:
        """Return (u, v) in m/s at time t_hours from start."""
        angle = np.radians(
            self.rotation_amplitude_deg
            * np.sin(2 * np.pi * t_hours / self.rotation_period_hours)
        )
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        u = self.base_u * cos_a - self.base_v * sin_a
        v = self.base_u * sin_a + self.base_v * cos_a
        return u, v


@dataclass
class WindField:
    """Synthetic wind field — spatially uniform, temporally varying."""
    base_u: float  # base eastward 10m wind (m/s)
    base_v: float  # base northward 10m wind (m/s)
    variability: float = 3.0  # m/s amplitude of random variation

    def velocity_at(self, t_hours: float) -> Tuple[float, float]:
        """Return (u_wind, v_wind) in m/s at time t_hours."""
        # Slowly varying sinusoidal + small random component
        phase = 2 * np.pi * t_hours / 36.0
        u = self.base_u + self.variability * np.sin(phase)
        v = self.base_v + self.variability * np.cos(phase * 0.7)
        return u, v


@dataclass
class VesselTrack:
    """A vessel track: arrays of (lon, lat, time_hours)."""
    name: str
    lons: np.ndarray
    lats: np.ndarray
    times: np.ndarray  # hours from reference time
    is_guilty: bool = False


# ─── Particle Advection ─────────────────────────────────────────────────────

def advect_particles(
    lons: np.ndarray,
    lats: np.ndarray,
    current: CurrentField,
    wind: WindField,
    wind_drift_factor: float,
    diffusivity: float,
    duration_hours: float,
    dt_seconds: float,
    current_noise_factor: float = 1.0,
    current_angle_noise_deg: float = 0.0,
    start_time_hours: float = 0.0,
    backward: bool = False,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Advect particles through the current+wind field.

    Returns:
        history_lons: shape (N, T) — lon at each timestep
        history_lats: shape (N, T) — lat at each timestep
        history_times: shape (T,) — time in hours at each timestep
    """
    N = len(lons)
    direction = -1.0 if backward else 1.0
    dt = dt_seconds * direction  # negative for backward

    n_steps = int(abs(duration_hours * 3600 / dt_seconds))
    history_lons = np.zeros((N, n_steps + 1))
    history_lats = np.zeros((N, n_steps + 1))
    history_times = np.zeros(n_steps + 1)

    history_lons[:, 0] = lons.copy()
    history_lats[:, 0] = lats.copy()
    history_times[0] = start_time_hours

    cur_lons = lons.copy()
    cur_lats = lats.copy()

    # Precompute current rotation noise
    angle_noise_rad = np.radians(current_angle_noise_deg)

    for step in range(1, n_steps + 1):
        t_hours = start_time_hours + (step * dt / 3600.0)

        # Get base current velocity
        u_curr, v_curr = current.velocity_at(t_hours)

        # Apply ensemble perturbation: scale + rotate
        u_curr *= current_noise_factor
        v_curr *= current_noise_factor
        if current_angle_noise_deg > 0:
            cos_n = np.cos(angle_noise_rad)
            sin_n = np.sin(angle_noise_rad)
            u_new = u_curr * cos_n - v_curr * sin_n
            v_new = u_curr * sin_n + v_curr * cos_n
            u_curr, v_curr = u_new, v_new

        # Get wind velocity
        u_wind, v_wind = wind.velocity_at(t_hours)

        # Total velocity = current + wind_drift_factor * wind
        u_total = u_curr + wind_drift_factor * u_wind
        v_total = v_curr + wind_drift_factor * v_wind

        # Deterministic displacement (m)
        dx = u_total * dt
        dy = v_total * dt

        # Stochastic diffusion (Brownian motion)
        sigma = np.sqrt(2 * diffusivity * abs(dt_seconds))
        dx += np.random.normal(0, sigma, N)
        dy += np.random.normal(0, sigma, N)

        # Convert to degrees
        cos_lat = np.cos(np.radians(cur_lats))
        cos_lat = np.maximum(cos_lat, 0.01)  # avoid division by zero at poles
        dlon = dx / (DEG_TO_M * cos_lat)
        dlat = dy / DEG_TO_M

        cur_lons += dlon
        cur_lats += dlat

        history_lons[:, step] = cur_lons
        history_lats[:, step] = cur_lats
        history_times[step] = t_hours

    return history_lons, history_lats, history_times


# ─── Forward Simulation (the "crime") ───────────────────────────────────────

def simulate_release(
    release_lon: float,
    release_lat: float,
    release_time_hours: float,
    slick_age_hours: float,
    n_particles: int,
    current: CurrentField,
    wind: WindField,
    wind_drift_factor: float = 0.03,
    diffusivity: float = 10.0,
    release_radius_deg: float = 0.005,  # ~500m spread
    dt_seconds: float = 900.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate oil release: seed particles and drift them forward.

    Returns:
        obs_lons, obs_lats: particle positions at observation time
    """
    # Seed particles with slight spatial spread (simulating discharge)
    lons = release_lon + np.random.normal(0, release_radius_deg, n_particles)
    lats = release_lat + np.random.normal(0, release_radius_deg, n_particles)

    history_lons, history_lats, _ = advect_particles(
        lons, lats, current, wind,
        wind_drift_factor=wind_drift_factor,
        diffusivity=diffusivity,
        duration_hours=slick_age_hours,
        dt_seconds=dt_seconds,
        start_time_hours=release_time_hours,
        backward=False,
    )

    # Return final positions = "the observed slick"
    return history_lons[:, -1], history_lats[:, -1]


# ─── Backward Ensemble ──────────────────────────────────────────────────────

@dataclass
class EnsembleMember:
    """Parameters for one ensemble member."""
    wind_drift_factor: float
    diffusivity: float
    current_noise_factor: float
    current_angle_noise_deg: float


def run_backward_ensemble(
    obs_lons: np.ndarray,
    obs_lats: np.ndarray,
    obs_time_hours: float,
    backward_duration_hours: float,
    n_particles_per_member: int,
    n_members: int,
    current: CurrentField,
    wind: WindField,
    dt_seconds: float = 900.0,
    forcing_error_level: str = "medium",
) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Run the backward ensemble: M members, each with perturbed forcing.

    forcing_error_level: "low" (±5%), "medium" (±20%), "high" (±40%)

    Returns:
        List of (history_lons, history_lats, history_times) per member
    """
    # Define perturbation ranges based on error level
    perturbation_ranges = {
        "low":    {"wdf": (0.025, 0.035), "diff": (5, 20),  "cnf": (0.95, 1.05), "cad": 5},
        "medium": {"wdf": (0.02, 0.04),  "diff": (5, 50),  "cnf": (0.80, 1.20), "cad": 15},
        "high":   {"wdf": (0.015, 0.05), "diff": (5, 100), "cnf": (0.60, 1.40), "cad": 30},
    }
    pr = perturbation_ranges[forcing_error_level]

    results = []
    n_obs = len(obs_lons)

    for m in range(n_members):
        # Sample perturbation parameters for this member
        member = EnsembleMember(
            wind_drift_factor=np.random.uniform(*pr["wdf"]),
            diffusivity=np.random.uniform(*pr["diff"]),
            current_noise_factor=np.random.uniform(*pr["cnf"]),
            current_angle_noise_deg=np.random.uniform(-pr["cad"], pr["cad"]),
        )

        # Subsample observed slick positions for this member
        if n_particles_per_member < n_obs:
            indices = np.random.choice(n_obs, n_particles_per_member, replace=False)
        else:
            indices = np.arange(n_obs)

        lons = obs_lons[indices]
        lats = obs_lats[indices]

        # Run backward
        hist_lons, hist_lats, hist_times = advect_particles(
            lons, lats, current, wind,
            wind_drift_factor=member.wind_drift_factor,
            diffusivity=member.diffusivity,
            duration_hours=backward_duration_hours,
            dt_seconds=dt_seconds,
            current_noise_factor=member.current_noise_factor,
            current_angle_noise_deg=member.current_angle_noise_deg,
            start_time_hours=obs_time_hours,
            backward=True,
        )

        results.append((hist_lons, hist_lats, hist_times))

    return results


# ─── Φ Field Construction ───────────────────────────────────────────────────

@dataclass
class PhiField:
    """
    The origin probability field Φ(x, y, t).
    Stored as a collection of 2D KDEs, one per time bin.
    """
    time_bins: np.ndarray  # center of each time bin (hours)
    bin_width_hours: float
    kdes: Dict[int, gaussian_kde]  # time_bin_index → KDE
    particle_counts: Dict[int, int]  # time_bin_index → number of particles

    def evaluate(self, lon: float, lat: float, t_hours: float) -> float:
        """Evaluate Φ at a single point (lon, lat, t)."""
        # Find the closest time bin
        bin_idx = np.argmin(np.abs(self.time_bins - t_hours))
        if bin_idx not in self.kdes:
            return 0.0

        try:
            return float(self.kdes[bin_idx]([[lon], [lat]])[0])
        except Exception:
            return 0.0

    def evaluate_batch(self, lons: np.ndarray, lats: np.ndarray,
                       t_hours: float) -> np.ndarray:
        """Evaluate Φ at multiple points for a single time."""
        bin_idx = np.argmin(np.abs(self.time_bins - t_hours))
        if bin_idx not in self.kdes:
            return np.zeros(len(lons))

        try:
            points = np.vstack([lons, lats])
            return self.kdes[bin_idx](points)
        except Exception:
            return np.zeros(len(lons))


def build_phi_field(
    ensemble_results: List[Tuple[np.ndarray, np.ndarray, np.ndarray]],
    bin_width_hours: float = 1.0,
    kde_bandwidth: Optional[float] = None,
    min_particles: int = 20,
) -> PhiField:
    """
    Build the Φ field from backward ensemble results.

    Collects all backward particle positions, bins them by time,
    and fits a 2D KDE for each time bin.
    """
    # Collect all particles from all ensemble members
    all_lons = []
    all_lats = []
    all_times = []

    for hist_lons, hist_lats, hist_times in ensemble_results:
        n_particles, n_steps = hist_lons.shape
        for step in range(n_steps):
            t = hist_times[step]
            all_lons.append(hist_lons[:, step])
            all_lats.append(hist_lats[:, step])
            all_times.append(np.full(n_particles, t))

    all_lons = np.concatenate(all_lons)
    all_lats = np.concatenate(all_lats)
    all_times = np.concatenate(all_times)

    # Determine time bins
    t_min, t_max = all_times.min(), all_times.max()
    n_bins = max(1, int(np.ceil((t_max - t_min) / bin_width_hours)))
    bin_edges = np.linspace(t_min, t_max, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    # Build KDE for each time bin
    kdes = {}
    particle_counts = {}

    for i in range(n_bins):
        mask = (all_times >= bin_edges[i]) & (all_times < bin_edges[i + 1])
        lons_bin = all_lons[mask]
        lats_bin = all_lats[mask]

        particle_counts[i] = len(lons_bin)

        if len(lons_bin) < min_particles:
            continue

        try:
            points = np.vstack([lons_bin, lats_bin])

            # Auto bandwidth or specified
            bw = kde_bandwidth if kde_bandwidth else "scott"

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kde = gaussian_kde(points, bw_method=bw)
                kdes[i] = kde
        except (np.linalg.LinAlgError, ValueError):
            # Singular matrix — particles too concentrated, skip
            continue

    return PhiField(
        time_bins=bin_centers,
        bin_width_hours=bin_width_hours,
        kdes=kdes,
        particle_counts=particle_counts,
    )


# ─── Vessel Track Generation ────────────────────────────────────────────────

def generate_straight_track(
    start_lon: float,
    start_lat: float,
    speed_knots: float,
    heading_deg: float,
    start_time_hours: float,
    duration_hours: float,
    n_points: int = 100,
    name: str = "vessel",
    is_guilty: bool = False,
) -> VesselTrack:
    """Generate a straight-line vessel track."""
    times = np.linspace(start_time_hours, start_time_hours + duration_hours, n_points)
    speed_ms = speed_knots * KNOTS_TO_MS
    heading_rad = np.radians(heading_deg)

    dx_ms = speed_ms * np.sin(heading_rad)  # eastward
    dy_ms = speed_ms * np.cos(heading_rad)  # northward

    lons = np.zeros(n_points)
    lats = np.zeros(n_points)
    lons[0] = start_lon
    lats[0] = start_lat

    for i in range(1, n_points):
        dt = (times[i] - times[i - 1]) * 3600  # hours to seconds
        cos_lat = np.cos(np.radians(lats[i - 1]))
        lons[i] = lons[i - 1] + (dx_ms * dt) / (DEG_TO_M * max(cos_lat, 0.01))
        lats[i] = lats[i - 1] + (dy_ms * dt) / DEG_TO_M

    return VesselTrack(name=name, lons=lons, lats=lats, times=times, is_guilty=is_guilty)


def generate_curving_track(
    start_lon: float,
    start_lat: float,
    speed_knots: float,
    initial_heading_deg: float,
    turn_rate_deg_per_hour: float,
    start_time_hours: float,
    duration_hours: float,
    n_points: int = 100,
    name: str = "vessel",
    is_guilty: bool = False,
) -> VesselTrack:
    """Generate a curving vessel track (gradual turn)."""
    times = np.linspace(start_time_hours, start_time_hours + duration_hours, n_points)
    speed_ms = speed_knots * KNOTS_TO_MS

    lons = np.zeros(n_points)
    lats = np.zeros(n_points)
    lons[0] = start_lon
    lats[0] = start_lat

    for i in range(1, n_points):
        dt = (times[i] - times[i - 1]) * 3600
        elapsed_hours = times[i] - start_time_hours
        heading = initial_heading_deg + turn_rate_deg_per_hour * elapsed_hours
        heading_rad = np.radians(heading)

        dx_ms = speed_ms * np.sin(heading_rad)
        dy_ms = speed_ms * np.cos(heading_rad)

        cos_lat = np.cos(np.radians(lats[i - 1]))
        lons[i] = lons[i - 1] + (dx_ms * dt) / (DEG_TO_M * max(cos_lat, 0.01))
        lats[i] = lats[i - 1] + (dy_ms * dt) / DEG_TO_M

    return VesselTrack(name=name, lons=lons, lats=lats, times=times, is_guilty=is_guilty)


def generate_guilty_track(
    release_lon: float,
    release_lat: float,
    release_time_hours: float,
    speed_knots: float = 12.0,
    heading_deg: Optional[float] = None,
    duration_hours: float = 12.0,
) -> VesselTrack:
    """
    Generate a guilty vessel track that passes through the release point
    at the release time.
    """
    if heading_deg is None:
        heading_deg = np.random.uniform(0, 360)

    speed_ms = speed_knots * KNOTS_TO_MS
    heading_rad = np.radians(heading_deg)

    # Calculate where the vessel was 'before' hours before the release
    hours_before = duration_hours / 2
    dx = speed_ms * np.sin(heading_rad) * hours_before * 3600
    dy = speed_ms * np.cos(heading_rad) * hours_before * 3600

    cos_lat = np.cos(np.radians(release_lat))
    start_lon = release_lon - dx / (DEG_TO_M * max(cos_lat, 0.01))
    start_lat = release_lat - dy / DEG_TO_M
    start_time = release_time_hours - hours_before

    return generate_straight_track(
        start_lon, start_lat, speed_knots, heading_deg,
        start_time, duration_hours,
        name="GUILTY",
        is_guilty=True,
    )


def generate_traffic(
    n_vessels: int,
    center_lon: float,
    center_lat: float,
    area_radius_deg: float,
    time_window_start: float,
    time_window_end: float,
    release_lon: float,
    release_lat: float,
    release_time_hours: float,
    min_distance_deg: float = 0.02,
) -> List[VesselTrack]:
    """
    Generate N innocent vessel tracks in the vicinity.

    Tracks are random straight or curving lines that pass through the
    general area but NOT through the exact release point at release time.
    """
    vessels = []

    for i in range(n_vessels):
        # Random start position within the area
        start_lon = center_lon + np.random.uniform(-area_radius_deg, area_radius_deg)
        start_lat = center_lat + np.random.uniform(-area_radius_deg, area_radius_deg)

        speed = np.random.uniform(6, 20)  # 6-20 knots
        heading = np.random.uniform(0, 360)
        start_time = np.random.uniform(time_window_start, time_window_end - 6)
        duration = np.random.uniform(6, 18)

        # Randomly choose straight or curving
        if np.random.random() < 0.3:
            turn_rate = np.random.uniform(-5, 5)  # deg/hour
            track = generate_curving_track(
                start_lon, start_lat, speed, heading, turn_rate,
                start_time, duration,
                name=f"vessel_{i:03d}",
            )
        else:
            track = generate_straight_track(
                start_lon, start_lat, speed, heading,
                start_time, duration,
                name=f"vessel_{i:03d}",
            )

        vessels.append(track)

    return vessels


# ─── Path-Integral Scoring ──────────────────────────────────────────────────

def compute_path_integral(
    track: VesselTrack,
    phi: PhiField,
) -> float:
    """
    Compute L_k = ∫ Φ(x_k(t), y_k(t), t) dt for a single vessel track.

    This is the core scoring mechanism: walk along the vessel's trajectory
    and sum up how much origin probability it passes through.
    """
    score = 0.0
    n_points = len(track.times)

    for i in range(n_points):
        t = track.times[i]

        # Only score within the Φ field's time range
        if t < phi.time_bins[0] - phi.bin_width_hours or \
           t > phi.time_bins[-1] + phi.bin_width_hours:
            continue

        phi_val = phi.evaluate(track.lons[i], track.lats[i], t)

        # Weight by time step (trapezoidal-ish integration)
        if i < n_points - 1:
            dt = abs(track.times[i + 1] - track.times[i])
        else:
            dt = abs(track.times[i] - track.times[i - 1]) if i > 0 else 0
        score += phi_val * dt

    return score


def compute_posterior(
    tracks: List[VesselTrack],
    phi: PhiField,
    emission_priors: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Compute the normalised posterior over all vessels + latent source.

    Returns dict of {vessel_name: probability, "LATENT_SOURCE": probability}
    """
    # Compute path-integral likelihood for each track
    likelihoods = {}
    for track in tracks:
        L_k = compute_path_integral(track, phi)

        # Apply emission prior if provided
        prior = 1.0
        if emission_priors and track.name in emission_priors:
            prior = emission_priors[track.name]

        likelihoods[track.name] = prior * L_k

    # Latent-source hypothesis L₀:
    # Residual Φ mass not explained by any track
    # Approximated as: total Φ mass minus sum of path integrals
    total_phi_mass = sum(likelihoods.values())

    # Use a constant base for L₀ (the "prior" that a dark vessel exists)
    # This is proportional to how much Φ is NOT covered by any track
    if total_phi_mass > 0:
        # L₀ = fraction of Φ field not traversed by any vessel × a scale factor
        # Simple approximation: use the mean likelihood as a reference
        mean_L = total_phi_mass / max(len(tracks), 1)
        L_0 = mean_L * 0.5  # prior belief that dark vessel is 50% as likely as average
    else:
        L_0 = 1.0  # no tracks have any signal → dark vessel gets some mass

    likelihoods["LATENT_SOURCE"] = L_0

    # Normalise into posterior
    total = sum(likelihoods.values())
    if total == 0:
        # Completely flat — uniform posterior
        n = len(likelihoods)
        return {name: 1.0 / n for name in likelihoods}

    posterior = {name: L / total for name, L in likelihoods.items()}
    return posterior


# ─── Nearest-Vessel Baseline ────────────────────────────────────────────────

def nearest_vessel_baseline(
    tracks: List[VesselTrack],
    slick_centroid_lon: float,
    slick_centroid_lat: float,
    obs_time_hours: float,
) -> str:
    """
    Baseline: pick the vessel closest to the slick centroid at observation time.
    This is roughly what Cerulean-style geometric matching does.
    """
    best_name = None
    best_dist = float("inf")

    for track in tracks:
        # Find the track point closest in time to observation
        time_idx = np.argmin(np.abs(track.times - obs_time_hours))

        # Compute distance to slick centroid
        dlon = (track.lons[time_idx] - slick_centroid_lon) * DEG_TO_M * \
               np.cos(np.radians(slick_centroid_lat))
        dlat = (track.lats[time_idx] - slick_centroid_lat) * DEG_TO_M
        dist = np.sqrt(dlon ** 2 + dlat ** 2)

        if dist < best_dist:
            best_dist = dist
            best_name = track.name

    return best_name


# ─── Single Trial ────────────────────────────────────────────────────────────

@dataclass
class TrialResult:
    """Result of a single go/no-go trial."""
    slick_age_hours: float
    n_vessels: int
    forcing_error: str
    trial_id: int
    top1_correct: bool
    top3_correct: bool
    baseline_correct: bool
    guilty_rank: int
    guilty_probability: float
    latent_probability: float
    top1_name: str
    posterior: Dict[str, float]


def run_single_trial(
    slick_age_hours: float,
    n_vessels: int,
    forcing_error: str,
    trial_id: int,
    release_lon: float = 72.0,
    release_lat: float = 15.0,
    n_forward_particles: int = 500,
    n_backward_particles_per_member: int = 200,
    n_ensemble_members: int = 30,
    dt_seconds: float = 900.0,
) -> TrialResult:
    """
    Run a single go/no-go trial:
    1. Simulate a release (forward drift)
    2. Run backward ensemble
    3. Build Φ
    4. Generate vessel tracks (1 guilty + N-1 innocent)
    5. Score all tracks
    6. Check if guilty vessel is correctly identified
    """
    # Setup environment
    current = CurrentField(
        base_u=0.25 + np.random.normal(0, 0.05),
        base_v=0.10 + np.random.normal(0, 0.05),
        rotation_period_hours=np.random.uniform(36, 60),
        rotation_amplitude_deg=np.random.uniform(10, 25),
    )
    wind = WindField(
        base_u=-6.0 + np.random.normal(0, 1),
        base_v=2.0 + np.random.normal(0, 1),
    )

    release_time = 0.0
    obs_time = release_time + slick_age_hours

    # ─── Phase 1: Simulate the crime (forward drift) ───
    obs_lons, obs_lats = simulate_release(
        release_lon, release_lat, release_time, slick_age_hours,
        n_forward_particles, current, wind,
        dt_seconds=dt_seconds,
    )

    # ─── Phase 2: Backward ensemble ───
    backward_duration = slick_age_hours * 1.3  # go back a bit further
    ensemble_results = run_backward_ensemble(
        obs_lons, obs_lats, obs_time, backward_duration,
        n_backward_particles_per_member, n_ensemble_members,
        current, wind,
        dt_seconds=dt_seconds,
        forcing_error_level=forcing_error,
    )

    # ─── Phase 3: Build Φ ───
    phi = build_phi_field(
        ensemble_results,
        bin_width_hours=max(0.5, slick_age_hours / 10),
    )

    # ─── Phase 4: Generate vessel tracks ───
    guilty_track = generate_guilty_track(
        release_lon, release_lat, release_time,
        speed_knots=np.random.uniform(8, 16),
    )

    # Generate innocent traffic
    area_radius = max(0.3, slick_age_hours * 0.02)  # wider area for older slicks
    innocent_tracks = generate_traffic(
        n_vessels=n_vessels - 1,
        center_lon=release_lon,
        center_lat=release_lat,
        area_radius_deg=area_radius,
        time_window_start=release_time - slick_age_hours,
        time_window_end=obs_time + 6,
        release_lon=release_lon,
        release_lat=release_lat,
        release_time_hours=release_time,
    )

    all_tracks = [guilty_track] + innocent_tracks

    # ─── Phase 5: Score all tracks ───
    posterior = compute_posterior(all_tracks, phi)

    # ─── Phase 6: Evaluate ───
    # Sort by probability (descending), excluding latent source for ranking
    vessel_posterior = {k: v for k, v in posterior.items() if k != "LATENT_SOURCE"}
    ranked = sorted(vessel_posterior.items(), key=lambda x: x[1], reverse=True)

    top1_name = ranked[0][0]
    top3_names = [r[0] for r in ranked[:3]]

    guilty_prob = posterior.get("GUILTY", 0.0)
    latent_prob = posterior.get("LATENT_SOURCE", 0.0)

    # Find guilty vessel's rank
    guilty_rank = next(
        (i + 1 for i, (name, _) in enumerate(ranked) if name == "GUILTY"),
        len(ranked) + 1
    )

    # Baseline: nearest vessel to slick centroid
    slick_centroid_lon = np.mean(obs_lons)
    slick_centroid_lat = np.mean(obs_lats)
    baseline_pick = nearest_vessel_baseline(
        all_tracks, slick_centroid_lon, slick_centroid_lat, obs_time
    )

    return TrialResult(
        slick_age_hours=slick_age_hours,
        n_vessels=n_vessels,
        forcing_error=forcing_error,
        trial_id=trial_id,
        top1_correct=(top1_name == "GUILTY"),
        top3_correct=("GUILTY" in top3_names),
        baseline_correct=(baseline_pick == "GUILTY"),
        guilty_rank=guilty_rank,
        guilty_probability=guilty_prob,
        latent_probability=latent_prob,
        top1_name=top1_name,
        posterior=posterior,
    )
